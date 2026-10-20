"""Rutas HTTP del modulo busqueda - dueno P2.

Todo cuelga de /api/busqueda. Son de lectura y no piden token: un visitante
tiene que poder ver que profesores hay antes de registrarse.
"""

from fastapi import APIRouter, Depends, Query

from app.dependencias import Db
from app.errores import ErrorAPI
from app.modulos.busqueda import esquemas, logica

router = APIRouter(prefix="/busqueda", tags=["busqueda"])


@router.get("/profesores", response_model=esquemas.PaginaBusqueda)
def buscar_profesores(db: Db, filtros: esquemas.FiltrosBusqueda = Depends()):
    """La busqueda de 1c con los nueve filtros combinables.

    Los filtros llegan como query params gracias a Depends(): ?materia=3&barrio=7
    se mapea solo al modelo FiltrosBusqueda.

    La ruta solo traduce query params al esquema; las reglas viven en logica.
    """
    return logica.buscar(db, filtros)


@router.get("/profesores/mapa", response_model=list[esquemas.PinMapa])
def profesores_en_mapa(
    db: Db,
    filtros: esquemas.FiltrosBusqueda = Depends(),
    ids: str | None = Query(None, description="ids separados por coma, para el mini mapa de 1f"),
):
    """Coordenadas para Leaflet. Compartido por 1a, 1c y 1f.

    El mini mapa de la ficha es este mismo endpoint con un solo id: Leaflet
    consume lo mismo en los tres casos.

    Si vienen ids, se ignoran los filtros. Se aceptan hasta cien ids positivos
    separados por coma y se conserva el orden pedido.
    """
    if ids is not None:
        return logica.pines_mapa(db, ids=_ids_desde_texto(ids))
    return logica.pines_mapa(db, filtros=filtros)


@router.get("/cercanos", response_model=list[esquemas.ProfesorCercano])
def profesores_cercanos(
    db: Db,
    barrio: int | None = Query(None, gt=0),
    centro_id: int | None = Query(None, gt=0),
    con_hueco: bool = False,
    limite: int = Query(5, ge=1, le=100),
):
    """Carrusel "Profes cerca de ti" de 1a, ordenado por cercania.

    El centro tiene prioridad como punto de referencia si vienen los dos.
    """
    return logica.cercanos(db, barrio, centro_id, con_hueco, limite)


@router.get("/mejor-puntuados", response_model=list[esquemas.ProfesorCercano])
def profesores_mejor_puntuados(
    db: Db,
    etapa: int | None = Query(None, gt=0),
    limite: int = Query(3, ge=1, le=100),
):
    """Los tres mejor rankeados del momento, para el podio de 1a.

    Exige al menos cinco resenas para entrar al ranking.
    """
    return logica.mejor_puntuados(db, etapa, limite)


def _ids_desde_texto(texto: str) -> list[int]:
    """Convierte ``"4,7,9"`` en ids unicos; 400 si el formato es invalido."""
    partes = [parte.strip() for parte in texto.split(",")]
    if not partes or any(not parte for parte in partes):
        raise ErrorAPI(400, "ids_invalidos")
    try:
        ids = [int(parte) for parte in partes]
    except ValueError as error:
        raise ErrorAPI(400, "ids_invalidos") from error
    if any(id_ <= 0 for id_ in ids):
        raise ErrorAPI(400, "ids_invalidos")
    ids = list(dict.fromkeys(ids))
    if len(ids) > 100:
        raise ErrorAPI(400, "demasiados_ids")
    return ids
