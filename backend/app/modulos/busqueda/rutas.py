"""Rutas HTTP del modulo busqueda - dueno P2.

Todo cuelga de /api/busqueda. Son de lectura y no piden token: un visitante
tiene que poder ver que profesores hay antes de registrarse.
"""

from fastapi import APIRouter, Depends, Query

from app.dependencias import Db
from app.modulos.busqueda import esquemas

router = APIRouter(prefix="/busqueda", tags=["busqueda"])


@router.get("/profesores", response_model=esquemas.PaginaBusqueda)
def buscar_profesores(db: Db, filtros: esquemas.FiltrosBusqueda = Depends()):
    """La busqueda de 1c con los nueve filtros combinables.

    Los filtros llegan como query params gracias a Depends(): ?materia=3&barrio=7
    se mapea solo al modelo FiltrosBusqueda.

    TODO (P2): implementar. Envolver logica.buscar(db, filtros).
    """
    raise NotImplementedError("P2 - busqueda: GET /busqueda/profesores")


@router.get("/profesores/mapa", response_model=list[esquemas.PinMapa])
def profesores_en_mapa(
    db: Db,
    filtros: esquemas.FiltrosBusqueda = Depends(),
    ids: str | None = Query(None, description="ids separados por coma, para el mini mapa de 1f"),
):
    """Coordenadas para Leaflet. Compartido por 1a, 1c y 1f.

    El mini mapa de la ficha es este mismo endpoint con un solo id: Leaflet
    consume lo mismo en los tres casos.

    TODO (P2): implementar. Si vienen ids, ignorar los filtros y devolver esos.
    """
    raise NotImplementedError("P2 - busqueda: GET /busqueda/profesores/mapa")


@router.get("/cercanos", response_model=list[esquemas.ProfesorCercano])
def profesores_cercanos(
    db: Db,
    barrio: int | None = None,
    centro_id: int | None = None,
    con_hueco: bool = False,
    limite: int = 5,
):
    """Carrusel "Profes cerca de ti" de 1a, ordenado por cercania.

    TODO (P2): implementar. Envolver logica.cercanos().
    """
    raise NotImplementedError("P2 - busqueda: GET /busqueda/cercanos")


@router.get("/mejor-puntuados", response_model=list[esquemas.ProfesorCercano])
def profesores_mejor_puntuados(db: Db, etapa: int | None = None, limite: int = 3):
    """Los tres mejor rankeados del momento, para el podio de 1a.

    TODO (P2): implementar. Envolver logica.mejor_puntuados().
    """
    raise NotImplementedError("P2 - busqueda: GET /busqueda/mejor-puntuados")
