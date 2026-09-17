"""Dependencias compartidas de FastAPI: quien es el usuario del token.

`yo` en la spec es siempre el usuario del token. Toda ruta que dice "solo el
token" usa `usuario_actual`. Las que ademas exigen un rol usan `solo_estudiante`
o `solo_profesor`.
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.enums import Rol
from app.errores import ErrorAPI
from app.seguridad import leer_token

# Alias para no repetir Depends(obtener_sesion) en cada firma.
Db = Annotated[Session, Depends(obtener_sesion)]


def usuario_actual(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
):
    """Resuelve el usuario del token de la cabecera Authorization.

    Espera `Authorization: Bearer <token>`.

    Devuelve el objeto Usuario (modelo del modulo cuentas).
    Levanta 401 si no hay token, si esta vencido o si la cuenta esta dada de baja.

    TODO (P1): implementar.
      1. Verificar que `authorization` empiece con "Bearer " y extraer el token.
      2. leer_token(token) -> si devuelve None, levantar ErrorAPI(401, "sin_token").
      3. Buscar el usuario por el id que viene en carga["sub"].
      4. Si no existe o su estado es 'dada_de_baja', levantar 401.
      5. Devolver el usuario.
    """
    raise NotImplementedError("P1 · cuentas: resolver el usuario del token")


# Alias que usan las rutas de todos los modulos.
Yo = Annotated[object, Depends(usuario_actual)]


def solo_estudiante(yo: Yo):
    """Igual que usuario_actual pero ademas exige rol estudiante (403 si no).

    Lo usan las rutas que solo tienen sentido del lado del alumno: checkout,
    tarjetas, perfil de estudiante.

    TODO (P1): implementar. Si yo.rol != Rol.estudiante -> ErrorAPI(403, "no_es_tuyo").
    """
    raise NotImplementedError("P1 · cuentas: exigir rol estudiante")


def solo_profesor(yo: Yo):
    """Igual que usuario_actual pero ademas exige rol profesor (403 si no).

    Lo usan la agenda, el panel y la edicion de la ficha publica.

    TODO (P1): implementar. Si yo.rol != Rol.profesor -> ErrorAPI(403, "no_es_tuyo").
    """
    raise NotImplementedError("P1 · cuentas: exigir rol profesor")
