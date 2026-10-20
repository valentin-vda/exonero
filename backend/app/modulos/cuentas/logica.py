"""Funciones publicas del modulo cuentas · dueno P1.

cuentas es la unica fuente de la identidad: nadie mas resuelve un token ni
busca un usuario por id. Los otros ocho modulos entran por aca.

Quien consume que:
  - dependencias -> obtener_usuario(), para resolver el usuario del token
  - todos        -> obtener_usuario() y datos_basicos(), para armar la
                    contraparte de una clase, el autor de un mensaje, la
                    persona de una resena
  - perfiles     -> datos_basicos(), datos_basicos_varios(), es_menor() y
                    validar_imagen_base64()
  - mensajeria   -> datos_basicos(), para la cabecera del hilo

COMO SE REPARTE EL TRABAJO ENTRE rutas.py Y logica.py (igual en perfiles):

  rutas.py   recibe la request, llama a estas funciones y hace el COMMIT.
  logica.py  las reglas: que se valida y que se guarda. NUNCA hace commit;
             como mucho flush, cuando necesita que la base le asigne el id.

Por que: el registro crea la cuenta (aca) y el perfil (en perfiles). Si cada
funcion hiciera su propio commit y la segunda fallara, quedaria una cuenta sin
perfil. Con el commit en la ruta, o se guardan las dos cosas o ninguna.
"""

import re
import secrets
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import seguridad
from app.enums import EstadoCuenta
from app.errores import ErrorAPI
from app.modulos.cuentas.modelos import Usuario


# ---------------------------------------------------------------------------
# Alta y login
# ---------------------------------------------------------------------------

def crear_cuenta(db: Session, datos, rol) -> Usuario:
    """Crea la fila en usuario y devuelve el Usuario creado.

    Lo llama el registro de los dos roles. No crea el perfil: de eso se ocupa
    el modulo perfiles, que es quien sabe que columnas lleva cada uno.

    `datos` es un RegistroIn (esquemas.py). El rol llega por parametro y NO
    sale del cuerpo: asi nadie se da de alta como profesor mandando un campo.
    """
    if _buscar_por_correo(db, datos.correo) is not None:
        raise ErrorAPI(409, "correo_ya_registrado")

    documento = _limpio(datos.documento)
    if documento and _documento_tomado(db, documento):
        raise ErrorAPI(409, "documento_ya_registrado")

    usuario = Usuario(
        correo=datos.correo,
        # La clave en texto plano no se guarda nunca: solo su hash bcrypt.
        hash_clave=seguridad.hashear_clave(datos.clave),
        nombre=datos.nombre.strip(),
        apellido=datos.apellido.strip(),
        documento=documento,
        telefono=_limpio(datos.telefono),
        fecha_nacimiento=datos.fecha_nacimiento,
        rol=rol,
    )
    db.add(usuario)
    # flush manda el INSERT a la base sin cerrar la transaccion. Hace falta
    # para que usuario.id tenga valor: el perfil lo necesita como clave foranea.
    db.flush()
    return usuario


def autenticar(db: Session, correo: str, clave: str) -> Usuario | None:
    """Devuelve el Usuario si las credenciales son correctas, o None.

    Devuelve None tanto si el correo no existe como si la clave esta mal: quien
    llama responde el mismo 409 credenciales_invalidas en los dos casos, para
    no revelar que correos estan registrados.
    """
    usuario = _buscar_por_correo(db, correo)
    if usuario is None or usuario.estado == EstadoCuenta.dada_de_baja:
        return None
    if not seguridad.verificar_clave(clave, usuario.hash_clave):
        return None
    return usuario


# ---------------------------------------------------------------------------
# Lectura: la usan los otros modulos
# ---------------------------------------------------------------------------

def obtener_usuario(db: Session, usuario_id: int) -> Usuario | None:
    """Devuelve un Usuario por id, o None si no existe.

    Es la funcion que mas se llama de todo el sistema: la usa
    dependencias.usuario_actual() en CADA request con token.
    """
    # db.get busca por clave primaria. Si el usuario ya se cargo en esta misma
    # request, lo devuelve de memoria sin volver a consultar.
    return db.get(Usuario, usuario_id)


def datos_basicos(db: Session, usuario_id: int) -> dict | None:
    """Version liviana de un usuario: id, nombre, apellido, foto y rol.

    Es lo que necesitan las tarjetas y las cabeceras de los otros modulos: la
    contraparte de una clase, la otra persona de un hilo. Devuelve un dict en
    vez del modelo, justamente para que nadie dependa de la forma de la tabla.
    """
    usuario = obtener_usuario(db, usuario_id)
    return _a_dict_basico(usuario) if usuario else None


def datos_basicos_varios(db: Session, ids: list[int]) -> dict[int, dict]:
    """Lo mismo que datos_basicos pero para varios usuarios en UNA consulta.

    Devuelve {id: datos}. La usa perfiles.ficha_resumida(), que arma listas de
    profesores: con una consulta por profesor seria lento (el problema "N+1").
    """
    if not ids:
        return {}
    usuarios = db.scalars(select(Usuario).where(Usuario.id.in_(ids)))
    return {u.id: _a_dict_basico(u) for u in usuarios}


def es_menor(db: Session, usuario_id: int) -> bool:
    """True si el usuario tiene menos de 18 anios segun fecha_nacimiento.

    Lo usa perfiles para decidir si el adulto responsable es obligatorio.
    Si fecha_nacimiento es NULL devuelve False: no se puede afirmar que es menor.
    """
    usuario = obtener_usuario(db, usuario_id)
    if usuario is None or usuario.fecha_nacimiento is None:
        return False
    return _edad(usuario.fecha_nacimiento, date.today()) < 18


# ---------------------------------------------------------------------------
# Recuperar la contrasena (sin correo saliente)
# ---------------------------------------------------------------------------

# Los codigos pendientes, en memoria del proceso:
#     {"ana@correo.com": {"codigo": "123456", "vence": datetime, "intentos": 0}}
# Es un dict y no una tabla a proposito: alcanza para el trabajo y no suma una
# migracion. La contra: se pierde si uvicorn se reinicia. Con --reload, guardar
# cualquier archivo .py reinicia el servidor; si pasa, se pide otro codigo.
_codigos: dict[str, dict] = {}

MINUTOS_VALIDEZ_CODIGO = 15
# Un codigo de 6 digitos tiene un millon de combinaciones. Sin un tope, un
# script podria probarlas todas en 15 minutos. Al quinto error se anula.
INTENTOS_MAXIMOS_CODIGO = 5


def generar_codigo_recuperacion(db: Session, correo: str) -> str | None:
    """Genera un codigo de 6 digitos para ese correo y lo devuelve.

    Devuelve None si el correo no corresponde a una cuenta activa. La ruta
    responde 200 igual en los dos casos (ver rutas.recuperar).
    """
    usuario = _buscar_por_correo(db, correo)
    if usuario is None or usuario.estado == EstadoCuenta.dada_de_baja:
        return None

    # secrets y no random: random es predecible, secrets esta hecho para esto.
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    _codigos[correo.lower()] = {
        "codigo": codigo,
        "vence": datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_VALIDEZ_CODIGO),
        "intentos": 0,
    }
    return codigo


def restablecer_clave(db: Session, correo: str, codigo: str, clave_nueva: str) -> None:
    """Si el codigo es valido, cambia la clave. Si no, 409 codigo_invalido.

    El codigo sirve UNA vez: se borra apenas se usa.
    """
    clave_dict = correo.lower()
    pendiente = _codigos.get(clave_dict)

    if pendiente is None or pendiente["vence"] < datetime.now(timezone.utc):
        _codigos.pop(clave_dict, None)
        raise ErrorAPI(409, "codigo_invalido")

    if pendiente["codigo"] != codigo.strip():
        pendiente["intentos"] += 1
        if pendiente["intentos"] >= INTENTOS_MAXIMOS_CODIGO:
            del _codigos[clave_dict]
        raise ErrorAPI(409, "codigo_invalido")

    usuario = _buscar_por_correo(db, correo)
    if usuario is None:
        raise ErrorAPI(409, "codigo_invalido")

    usuario.hash_clave = seguridad.hashear_clave(clave_nueva)
    del _codigos[clave_dict]


# ---------------------------------------------------------------------------
# La cuenta propia: lo que se edita desde 1e y 1j
# ---------------------------------------------------------------------------

def actualizar_datos(db: Session, usuario: Usuario, cambios: dict) -> None:
    """Aplica los cambios de PATCH /usuarios/yo.

    `cambios` trae SOLO los campos que mando el frontend (la ruta usa
    model_dump(exclude_unset=True)). Un campo que no vino no se toca; un campo
    que vino en null se borra (por ejemplo, quitar el telefono).
    """
    # nombre y apellido no pueden quedar vacios: son NOT NULL en la tabla.
    for campo in ("nombre", "apellido"):
        if campo in cambios:
            valor = _limpio(cambios[campo])
            if not valor:
                raise ErrorAPI(400, f"{campo}_requerido")
            setattr(usuario, campo, valor)

    if "documento" in cambios:
        documento = _limpio(cambios["documento"])
        # Solo se chequea si cambio: el propio documento no esta "tomado".
        if documento and documento != usuario.documento and _documento_tomado(db, documento):
            raise ErrorAPI(409, "documento_ya_registrado")
        usuario.documento = documento

    if "telefono" in cambios:
        usuario.telefono = _limpio(cambios["telefono"])

    if "fecha_nacimiento" in cambios:
        nacimiento = cambios["fecha_nacimiento"]
        if nacimiento is not None and nacimiento > date.today():
            raise ErrorAPI(400, "fecha_invalida")
        usuario.fecha_nacimiento = nacimiento


def cambiar_foto(db: Session, usuario: Usuario, foto_base64: str) -> None:
    """Guarda la foto de perfil (un data URL base64) despues de validarla."""
    validar_imagen_base64(foto_base64)
    usuario.foto_base64 = foto_base64


def cambiar_clave(db: Session, usuario: Usuario, clave_actual: str, clave_nueva: str) -> None:
    """Cambia la clave si la actual es correcta.

    Pedir la actual es lo que impide que alguien con un token robado (o con la
    pestania abierta en una compu ajena) se quede con la cuenta.
    """
    if not seguridad.verificar_clave(clave_actual, usuario.hash_clave):
        raise ErrorAPI(403, "clave_actual_incorrecta")
    usuario.hash_clave = seguridad.hashear_clave(clave_nueva)


def cambiar_tema(db: Session, usuario: Usuario, tema) -> None:
    """Claro u oscuro. El esquema TemaIn ya valido que sea uno de los dos."""
    usuario.tema = tema


def dar_de_baja(db: Session, usuario: Usuario) -> None:
    """Baja LOGICA: la cuenta queda inactiva, pero no se borra nada.

    Las clases pasadas, los cobros y las resenas tienen que seguir existiendo
    para la otra persona. Desde aca, autenticar() y usuario_actual() rechazan
    la cuenta, asi que el token que tenga abierto deja de servir.

    Pausar la ficha del profesor NO se hace aca sino en la ruta, que llama a
    perfiles: si este archivo importara perfiles y perfiles importa este, Python
    entraria en una importacion circular.
    """
    usuario.estado = EstadoCuenta.dada_de_baja


# ---------------------------------------------------------------------------
# Imagenes en base64 (fotos de perfil y fotos del lugar)
# ---------------------------------------------------------------------------

# Un data URL de imagen: "data:image/jpeg;base64,/9j/4AAQSk..."
_PATRON_IMAGEN = re.compile(r"^data:image/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+$")

# Unos 2 MB de imagen. En base64 cada 3 bytes ocupan 4 caracteres.
# El frontend achica las fotos antes de mandarlas (utiles/imagenes.js), asi
# que en la practica llegan muy por debajo de esto.
MAX_CARACTERES_IMAGEN = 2_800_000


def validar_imagen_base64(texto: str) -> None:
    """400 si no es un data URL de imagen, o si pesa demasiado.

    Las fotos van a la base como texto y viajan en cada GET /usuarios/yo: una
    foto de 10 MB haria lenta cada pantalla.
    """
    if len(texto) > MAX_CARACTERES_IMAGEN:
        raise ErrorAPI(400, "foto_muy_grande")
    if not _PATRON_IMAGEN.match(texto):
        raise ErrorAPI(400, "foto_invalida")


# ---------------------------------------------------------------------------
# Auxiliares privadas (el guion bajo dice "no la uses desde afuera")
# ---------------------------------------------------------------------------

def _buscar_por_correo(db: Session, correo: str) -> Usuario | None:
    # La columna es citext: la comparacion ignora mayusculas sola, asi que
    # "Ana@Correo.com" encuentra a "ana@correo.com" sin hacer nada mas.
    return db.scalar(select(Usuario).where(Usuario.correo == correo))


def _documento_tomado(db: Session, documento: str) -> bool:
    return db.scalar(select(Usuario.id).where(Usuario.documento == documento)) is not None


def _a_dict_basico(usuario: Usuario) -> dict:
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "apellido": usuario.apellido,
        "foto_base64": usuario.foto_base64,
        "rol": usuario.rol.value,
    }


def _limpio(texto: str | None) -> str | None:
    """Saca los espacios de los costados. Un texto vacio se guarda como NULL."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None


def _edad(nacimiento: date, hoy: date) -> int:
    # Se resta uno si este anio todavia no llego el cumpleanios.
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))
