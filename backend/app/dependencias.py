"""Dependencias compartidas de FastAPI: quien es el usuario del token.

`yo` en la spec es siempre el usuario del token. Toda ruta que dice "solo el
token" usa `usuario_actual`. Las que ademas exigen un rol usan `solo_estudiante`
o `solo_profesor`.

COMO FUNCIONA UNA DEPENDENCIA DE FASTAPI (para leer el resto del codigo):

    @router.get("/yo")
    def obtener_yo(yo: Yo, db: Db):
        ...

Antes de ejecutar obtener_yo, FastAPI mira los parametros. `Yo` dice
"Depends(usuario_actual)", asi que FastAPI llama primero a usuario_actual(),
que lee la cabecera Authorization y busca al usuario. Lo que esa funcion
devuelve llega a la ruta como `yo`. Si levanta un ErrorAPI, la ruta ni se
ejecuta y el cliente recibe el 401.

Lo mismo con `Db`: FastAPI abre una sesion de base con obtener_sesion() y la
cierra cuando termina la request.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.enums import EstadoCuenta, Rol
from app.errores import no_es_tuyo, sin_autorizacion
from app.modulos.cuentas import logica as cuentas
from app.seguridad import leer_token

# Alias para no repetir Depends(obtener_sesion) en cada firma.
Db = Annotated[Session, Depends(obtener_sesion)]


def usuario_actual(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
):
    """Resuelve el usuario del token de la cabecera Authorization.

    Espera `Authorization: Bearer <token>`, que es lo que manda
    frontend/src/api/cliente.js en cada llamada.

    Devuelve el objeto Usuario (modelo del modulo cuentas).
    Levanta 401 si no hay token, si esta vencido o si la cuenta esta dada de baja.
    """
    # 1. La cabecera tiene que existir y empezar con "Bearer ".
    if not authorization or not authorization.startswith("Bearer "):
        raise sin_autorizacion()
    token = authorization.removeprefix("Bearer ").strip()

    # 2. leer_token verifica la firma y el vencimiento. Si algo falla devuelve
    #    None (ver app/seguridad.py).
    carga = leer_token(token)
    if carga is None:
        raise sin_autorizacion()

    # 3. "sub" es el id del usuario; se guardo como texto al firmar el token.
    usuario = cuentas.obtener_usuario(db, int(carga["sub"]))

    # 4. Un token de una cuenta borrada o dada de baja ya no sirve, aunque la
    #    firma sea valida y no haya vencido.
    if usuario is None or usuario.estado == EstadoCuenta.dada_de_baja:
        raise sin_autorizacion()

    return usuario


# Alias que usan las rutas de todos los modulos.
Yo = Annotated[object, Depends(usuario_actual)]


def solo_estudiante(yo: Yo):
    """Igual que usuario_actual pero ademas exige rol estudiante (403 si no).

    Lo usan las rutas que solo tienen sentido del lado del alumno: checkout,
    tarjetas, perfil de estudiante.

    Se apoya en `Yo`: FastAPI primero resuelve el usuario (o corta con 401) y
    recien despues mira el rol.
    """
    if yo.rol != Rol.estudiante:
        raise no_es_tuyo()
    return yo


def solo_profesor(yo: Yo):
    """Igual que usuario_actual pero ademas exige rol profesor (403 si no).

    Lo usan la agenda, el panel y la edicion de la ficha publica.
    """
    if yo.rol != Rol.profesor:
        raise no_es_tuyo()
    return yo


# Alias para las rutas de un solo rol. Se usan igual que Yo:
#     def mi_ruta(yo: Estudiante, db: Db): ...
Estudiante = Annotated[object, Depends(solo_estudiante)]
Profesor = Annotated[object, Depends(solo_profesor)]
