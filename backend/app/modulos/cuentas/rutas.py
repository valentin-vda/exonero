"""Rutas HTTP del modulo cuentas - dueno P1.

Dos grupos:
  /api/auth/*       registro, login y recuperacion. Las UNICAS rutas sin token.
  /api/usuarios/yo  la cuenta propia. `yo` es siempre el usuario del token.

GET /usuarios/yo lo usan las diez pantallas: nadie mas resuelve el token ni
arma la cabecera.

COMO LEER UNA RUTA:

    @router_usuarios.put("/yo/clave", response_model=esquemas.OkOut)
    def cambiar_clave(datos: esquemas.ClaveIn, yo: Yo, db: Db):

  - El decorador dice el metodo y la URL. response_model es la forma de la
    respuesta: FastAPI la valida y la muestra en /docs.
  - `datos: esquemas.ClaveIn` es el cuerpo JSON. FastAPI lo valida contra el
    esquema ANTES de entrar; si falta un campo, responde 422 solo.
  - `yo: Yo` es el usuario del token (ver app/dependencias.py).
  - `db: Db` es la sesion de base.

Cada ruta hace lo mismo: llama a logica.py, hace el commit y responde.
"""

from fastapi import APIRouter, status

from app import seguridad
from app.dependencias import Db, Yo
from app.enums import Rol
from app.errores import ErrorAPI
from app.modulos.cuentas import esquemas, logica
from app.modulos.mensajeria import logica as mensajeria
from app.modulos.perfiles import logica as perfiles

# Dos routers porque son dos prefijos distintos; main.py monta los dos.
router_auth = APIRouter(prefix="/auth", tags=["auth"])
router_usuarios = APIRouter(prefix="/usuarios", tags=["cuentas"])


# ============================================================================
# /api/auth  -  sin token
# ============================================================================

@router_auth.post(
    "/registro/estudiante",
    response_model=esquemas.TokenOut,
    status_code=status.HTTP_201_CREATED,
)
def registro_estudiante(datos: esquemas.RegistroIn, db: Db):
    """Alta de una cuenta de estudiante. Crea usuario + perfil_estudiante vacio.

    Devuelve el token ya emitido, para que el frontend entre directo al tablero
    sin pedir el login de nuevo.

    Errores: 409 correo_ya_registrado, 409 documento_ya_registrado
    """
    return _registrar(db, datos, Rol.estudiante)


@router_auth.post(
    "/registro/profesor",
    response_model=esquemas.TokenOut,
    status_code=status.HTTP_201_CREATED,
)
def registro_profesor(datos: esquemas.RegistroIn, db: Db):
    """Alta de una cuenta de profesor. Crea usuario + perfil_profesor en borrador.

    La ficha nace en estado borrador: no aparece en la busqueda hasta que el
    profesor la completa y la publica desde 1j.
    """
    return _registrar(db, datos, Rol.profesor)


def _registrar(db, datos, rol) -> dict:
    """Lo comun a los dos registros. El rol viene de la RUTA, nunca del cuerpo."""
    # 1. La cuenta (cuentas) y el perfil vacio (perfiles), con flush y sin commit.
    usuario = logica.crear_cuenta(db, datos, rol)
    if rol == Rol.estudiante:
        perfiles.crear_perfil_estudiante(db, usuario.id)
    else:
        perfiles.crear_perfil_profesor(db, usuario.id)

    # 2. Un solo commit para las dos filas: o quedan las dos o ninguna.
    db.commit()

    # 3. El token, para entrar directo.
    return _respuesta_con_token(usuario)


@router_auth.post("/login", response_model=esquemas.TokenOut)
def login(datos: esquemas.LoginIn, db: Db):
    """Devuelve el token. No se guarda sesion: vive en el frontend y vence solo.

    Mismo error para correo inexistente y clave mala, para no revelar que
    correos estan registrados.
    """
    usuario = logica.autenticar(db, datos.correo, datos.clave)
    if usuario is None:
        raise ErrorAPI(409, "credenciales_invalidas")
    return _respuesta_con_token(usuario)


@router_auth.post("/recuperar", response_model=esquemas.OkOut)
def recuperar(datos: esquemas.RecuperarIn, db: Db):
    """Paso 1 de recuperar la contrasena: genera y muestra el codigo.

    No hay correo saliente, esta fuera de alcance: el codigo se imprime en la
    consola del backend (la terminal donde corre uvicorn) y de ahi lo copia
    quien esta probando.

    Responde 200 SIEMPRE, exista o no el correo, por la misma razon que el
    login: no revelar que cuentas existen.
    """
    codigo = logica.generar_codigo_recuperacion(db, datos.correo)
    if codigo is not None:
        # flush=True para que se vea al instante en la terminal de uvicorn.
        print(
            f"\n[Exonero] Codigo para recuperar la clave de {datos.correo}: {codigo}"
            f"  (vale {logica.MINUTOS_VALIDEZ_CODIGO} minutos)\n",
            flush=True,
        )
    return {"ok": True}


@router_auth.post("/restablecer", response_model=esquemas.OkOut)
def restablecer(datos: esquemas.RestablecerIn, db: Db):
    """Paso 2: con el codigo valido, fija la contrasena nueva.

    Error: 409 codigo_invalido (no existe, vencio, o ya se uso).
    """
    logica.restablecer_clave(db, datos.correo, datos.codigo, datos.clave_nueva)
    db.commit()
    return {"ok": True}


# ============================================================================
# /api/usuarios/yo  -  con token
# ============================================================================

@router_usuarios.get("/yo", response_model=esquemas.YoOut)
def obtener_yo(yo: Yo, db: Db):
    """El usuario del token. LAS DIEZ PANTALLAS lo llaman al entrar.

    Trae el contador de mensajes no leidos adentro para que la cabecera se arme
    con un solo llamado, y para el estudiante ademas su etapa, nivel, centro y
    barrio, que es lo que muestra el saludo de 1a.
    """
    return _armar_yo(db, yo)


@router_usuarios.patch("/yo", response_model=esquemas.YoOut)
def actualizar_yo(datos: esquemas.ActualizarUsuarioIn, yo: Yo, db: Db):
    """Datos de la persona. Compartido por 1e y 1j: son los mismos campos.

    PATCH y no PUT porque solo se tocan los campos que vienen. El correo no
    esta en el esquema de entrada: es la credencial y no se cambia.
    """
    # exclude_unset=True: solo los campos que el frontend mando de verdad.
    # Sin esto, los que no vinieron llegarian como None y se borrarian.
    logica.actualizar_datos(db, yo, datos.model_dump(exclude_unset=True))
    db.commit()
    return _armar_yo(db, yo)


@router_usuarios.put("/yo/foto", response_model=esquemas.OkOut)
def cambiar_foto(datos: esquemas.FotoIn, yo: Yo, db: Db):
    """Foto de perfil, en base64. Compartido por 1e y 1j.

    Errores: 400 foto_invalida (no es un data URL de imagen),
             400 foto_muy_grande (pasa de unos 2 MB).
    """
    logica.cambiar_foto(db, yo, datos.foto_base64)
    db.commit()
    return {"ok": True}


@router_usuarios.put("/yo/clave", response_model=esquemas.OkOut)
def cambiar_clave(datos: esquemas.ClaveIn, yo: Yo, db: Db):
    """Cambio de contrasena. Compartido por 1e y 1j.

    Error: 403 clave_actual_incorrecta.
    """
    logica.cambiar_clave(db, yo, datos.clave_actual, datos.clave_nueva)
    db.commit()
    return {"ok": True}


@router_usuarios.put("/yo/tema", response_model=esquemas.OkOut)
def cambiar_tema(datos: esquemas.TemaIn, yo: Yo, db: Db):
    """Tema claro u oscuro. Compartido por 1e y 1j.

    Se guarda en la cuenta, asi el tema sigue al usuario aunque entre desde
    otra computadora.
    """
    logica.cambiar_tema(db, yo, datos.tema)
    db.commit()
    return {"ok": True}


@router_usuarios.delete("/yo", status_code=status.HTTP_204_NO_CONTENT)
def darse_de_baja(yo: Yo, db: Db):
    """Baja LOGICA: la cuenta queda inactiva y las clases pasadas se conservan.

    Cerrar sesion no tiene endpoint: es descartar el token en el frontend.
    """
    logica.dar_de_baja(db, yo)
    # Si es profesor, su ficha sale de la busqueda. Va aca y no en logica para
    # no crear una importacion circular entre cuentas y perfiles.
    if yo.rol == Rol.profesor:
        perfiles.pausar_ficha(db, yo.id)
    db.commit()
    # 204 = "salio bien y no hay nada que devolver".
    return None


# ============================================================================
# Auxiliares de este archivo
# ============================================================================

def _respuesta_con_token(usuario) -> dict:
    """La forma de TokenOut: el token, cuando vence y un pedacito del usuario."""
    token, expira_en = seguridad.crear_token(usuario.id, usuario.rol.value)
    return {
        "token": token,
        "expira_en": expira_en,
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "rol": usuario.rol.value},
    }


def _armar_yo(db, yo) -> dict:
    """La forma de YoOut. La usan GET y PATCH /usuarios/yo."""
    return {
        "id": yo.id,
        "nombre": yo.nombre,
        "apellido": yo.apellido,
        "correo": yo.correo,
        "rol": yo.rol.value,
        "foto_base64": yo.foto_base64,
        "tema": yo.tema.value,
        "documento": yo.documento,
        "telefono": yo.telefono,
        "fecha_nacimiento": yo.fecha_nacimiento,
        "creado_el": yo.creado_el,
        "mensajes_no_leidos": _contar_no_leidos(db, yo.id),
        # Solo el estudiante tiene cabecera con etapa, centro y barrio.
        "estudiante": perfiles.cabecera_estudiante(db, yo.id) if yo.rol == Rol.estudiante else None,
    }


def _contar_no_leidos(db, usuario_id: int) -> int:
    """El contador de mensajes sin leer, que calcula mensajeria (P3).

    Mientras P3 no implemente contar_no_leidos(), esa funcion levanta
    NotImplementedError. Si dejaramos pasar ese error, GET /usuarios/yo
    devolveria 500 y nadie podria entrar a la app. Por eso, en ese caso
    puntual, se responde 0.

    Cuando P3 la termine, el except deja de activarse solo: no hay que tocar
    nada aca.
    """
    try:
        return mensajeria.contar_no_leidos(db, usuario_id)
    except NotImplementedError:
        return 0
