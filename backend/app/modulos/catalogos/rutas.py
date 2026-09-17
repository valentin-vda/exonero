"""Rutas HTTP del modulo catalogos · dueno P2.

Todo cuelga de /api/catalogos. Son listas publicas: no piden token.

Pantallas que las usan: 1a (centrar el mapa), 1c (poblar los nueve filtros),
1e y 1j (selectores de los dos perfiles).
"""

from fastapi import APIRouter

from app.dependencias import Db
from app.modulos.catalogos import esquemas

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/todo", response_model=esquemas.CatalogoCompletoOut)
def catalogo_completo(db: Db):
    """Materias, etapas, barrios, centros e idiomas en un solo llamado.

    Pantallas: 1a · 1c · 1e · 1j. El frontend lo pide una vez al entrar y lo
    cachea; estas listas casi no cambian.

    TODO (P2): implementar. Leer las cinco tablas y devolverlas juntas.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/todo")


@router.get("/barrios", response_model=list[esquemas.BarrioOut])
def listar_barrios(db: Db):
    """Barrios con su centroide.

    Pantallas: 1a · 1c · 1e · 1j. Leaflet usa latitud/longitud para centrar la
    vista inicial del mapa.

    TODO (P2): implementar. Devolver todos los barrios ordenados por nombre.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/barrios")


@router.get("/materias", response_model=list[esquemas.MateriaOut])
def listar_materias(db: Db):
    """Materias activas, ordenadas por nombre. Filtro principal de 1c.

    TODO (P2): implementar. Filtrar por activa = true.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/materias")


@router.get("/etapas", response_model=list[esquemas.EtapaOut])
def listar_etapas(db: Db):
    """Etapas educativas ordenadas por la columna `orden`.

    TODO (P2): implementar.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/etapas")


@router.get("/centros", response_model=list[esquemas.CentroOut])
def listar_centros(db: Db, barrio_id: int | None = None):
    """Centros educativos, opcionalmente filtrados por barrio.

    TODO (P2): implementar. Si viene barrio_id, filtrar por ese barrio.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/centros")


@router.get("/idiomas", response_model=list[esquemas.IdiomaOut])
def listar_idiomas(db: Db):
    """Idiomas en los que se puede dictar. Uno de los nueve filtros de 1c.

    TODO (P2): implementar.
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/idiomas")


@router.get("/parametros", response_model=esquemas.ParametrosOut)
def parametros(db: Db):
    """Comision de servicio y tasa de IVA vigentes.

    No lo pide ninguna pantalla directamente (el desglose siempre viene armado
    de POST /clases/cotizar), pero es util para depurar y para la defensa.

    TODO (P2): implementar. Envolver logica.parametros_vigentes(db).
    """
    raise NotImplementedError("P2 · catalogos: GET /catalogos/parametros")
