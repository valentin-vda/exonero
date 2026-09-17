"""Rutas HTTP del modulo cuentas - dueno P1.

Dos grupos:
  /api/auth/*       registro, login y recuperacion. Las UNICAS rutas sin token.
  /api/usuarios/yo  la cuenta propia. `yo` es siempre el usuario del token.

GET /usuarios/yo lo usan las diez pantallas: nadie mas resuelve el token ni
arma la cabecera.
"""

from fastapi import APIRouter, status

from app.dependencias import Db, Yo
from app.modulos.cuentas import esquemas

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

    TODO (P1): implementar.
      1. usuario = logica.crear_cuenta(db, datos, Rol.estudiante)
      2. perfiles.logica.crear_perfil_estudiante(db, usuario.id) -> perfil vacio
      3. db.commit() -> cuenta y perfil se crean juntos o no se crea ninguno
      4. token, expira = seguridad.crear_token(usuario.id, usuario.rol.value)
      5. Devolver TokenOut.
    Errores: 409 correo_ya_registrado, 409 documento_ya_registrado
    """
    raise NotImplementedError("P1 - cuentas: POST /auth/registro/estudiante")


@router_auth.post(
    "/registro/profesor",
    response_model=esquemas.TokenOut,
    status_code=status.HTTP_201_CREATED,
)
def registro_profesor(datos: esquemas.RegistroIn, db: Db):
    """Alta de una cuenta de profesor. Crea usuario + perfil_profesor en borrador.

    La ficha nace en estado borrador: no aparece en la busqueda hasta que el
    profesor la completa y la publica desde 1j.

    TODO (P1): implementar. Igual que el de estudiante pero con Rol.profesor y
    perfiles.logica.crear_perfil_profesor().
    """
    raise NotImplementedError("P1 - cuentas: POST /auth/registro/profesor")


@router_auth.post("/login", response_model=esquemas.TokenOut)
def login(datos: esquemas.LoginIn, db: Db):
    """Devuelve el token. No se guarda sesion: vive en el frontend y vence solo.

    TODO (P1): implementar.
      1. usuario = logica.autenticar(db, datos.correo, datos.clave)
      2. Si es None -> ErrorAPI(409, "credenciales_invalidas").
         Mismo error para correo inexistente y clave mala, para no revelar que
         correos estan registrados.
      3. Emitir el token y devolver TokenOut.
    """
    raise NotImplementedError("P1 - cuentas: POST /auth/login")


@router_auth.post("/recuperar", response_model=esquemas.OkOut)
def recuperar(datos: esquemas.RecuperarIn, db: Db):
    """Paso 1 de recuperar la contrasena: genera y muestra el codigo.

    No hay correo saliente, esta fuera de alcance: el codigo se imprime en la
    consola del backend y de ahi lo copia quien esta probando.

    Responde 200 SIEMPRE, exista o no el correo, por la misma razon que el
    login: no revelar que cuentas existen.

    TODO (P1): implementar.
      1. Buscar el usuario. Si no existe, devolver ok igual y no hacer nada mas.
      2. Generar un codigo de 6 digitos con validez corta, 15 minutos.
      3. Guardarlo. Lo mas simple es un dict en memoria del modulo: alcanza para
         el trabajo y evita una tabla nueva. Si prefieren tabla, va aca.
      4. Imprimirlo en consola con print().
    """
    raise NotImplementedError("P1 - cuentas: POST /auth/recuperar")


@router_auth.post("/restablecer", response_model=esquemas.OkOut)
def restablecer(datos: esquemas.RestablecerIn, db: Db):
    """Paso 2: con el codigo valido, fija la contrasena nueva.

    TODO (P1): implementar.
      1. Validar codigo y vencimiento -> 409 codigo_invalido si no.
      2. usuario.hash_clave = seguridad.hashear_clave(datos.clave_nueva)
      3. Invalidar el codigo usado para que no sirva dos veces.
    """
    raise NotImplementedError("P1 - cuentas: POST /auth/restablecer")


# ============================================================================
# /api/usuarios/yo  -  con token
# ============================================================================

@router_usuarios.get("/yo", response_model=esquemas.YoOut)
def obtener_yo(yo: Yo, db: Db):
    """El usuario del token. LAS DIEZ PANTALLAS lo llaman al entrar.

    Trae el contador de mensajes no leidos adentro para que la cabecera se arme
    con un solo llamado, y para el estudiante ademas su etapa, nivel, centro y
    barrio, que es lo que muestra el saludo de 1a.

    TODO (P1): implementar.
      1. Armar YoOut con los datos de yo.
      2. mensajes_no_leidos = mensajeria.logica.contar_no_leidos(db, yo.id)
      3. Si el rol es estudiante, pedirle a perfiles los datos de cabecera.
         Si es profesor, el bloque estudiante va en null.
    """
    raise NotImplementedError("P1 - cuentas: GET /usuarios/yo")


@router_usuarios.patch("/yo", response_model=esquemas.YoOut)
def actualizar_yo(datos: esquemas.ActualizarUsuarioIn, yo: Yo, db: Db):
    """Datos de la persona. Compartido por 1e y 1j: son los mismos campos.

    PATCH y no PUT porque solo se tocan los campos que vienen. El correo no
    esta en el esquema de entrada: es la credencial y no se cambia.

    TODO (P1): implementar.
      1. Aplicar solo los campos no nulos de datos.
      2. Si cambia el documento, verificar que no este tomado -> 409.
      3. Commit y devolver el mismo YoOut que GET /usuarios/yo.
    """
    raise NotImplementedError("P1 - cuentas: PATCH /usuarios/yo")


@router_usuarios.put("/yo/foto", response_model=esquemas.OkOut)
def cambiar_foto(datos: esquemas.FotoIn, yo: Yo, db: Db):
    """Foto de perfil, en base64. Compartido por 1e y 1j.

    TODO (P1): implementar.
      1. Validar que sea un data URL de imagen y que no pase de unos 2 MB: va a
         la base como texto y se arrastra en cada GET /usuarios/yo.
      2. Guardar en usuario.foto_base64.
    """
    raise NotImplementedError("P1 - cuentas: PUT /usuarios/yo/foto")


@router_usuarios.put("/yo/clave", response_model=esquemas.OkOut)
def cambiar_clave(datos: esquemas.ClaveIn, yo: Yo, db: Db):
    """Cambio de contrasena. Compartido por 1e y 1j.

    TODO (P1): implementar.
      1. verificar_clave(datos.clave_actual, yo.hash_clave) -> 403 si no.
      2. Guardar el hash de la nueva.
    """
    raise NotImplementedError("P1 - cuentas: PUT /usuarios/yo/clave")


@router_usuarios.put("/yo/tema", response_model=esquemas.OkOut)
def cambiar_tema(datos: esquemas.TemaIn, yo: Yo, db: Db):
    """Tema claro u oscuro. Compartido por 1e y 1j.

    TODO (P1): implementar. Validar que sea claro u oscuro y guardarlo.
    """
    raise NotImplementedError("P1 - cuentas: PUT /usuarios/yo/tema")


@router_usuarios.delete("/yo", status_code=status.HTTP_204_NO_CONTENT)
def darse_de_baja(yo: Yo, db: Db):
    """Baja LOGICA: la cuenta queda inactiva y las clases pasadas se conservan.

    Cerrar sesion no tiene endpoint: es descartar el token en el frontend.

    TODO (P1): implementar.
      1. yo.estado = EstadoCuenta.dada_de_baja
      2. Si es profesor, pasar su ficha a pausada para que salga de la busqueda.
      3. NO borrar nada: el historial y los cobros tienen que quedar.
    """
    raise NotImplementedError("P1 - cuentas: DELETE /usuarios/yo")
