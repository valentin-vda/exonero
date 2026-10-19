"""Rutas HTTP del modulo catalogos · dueno P2.

Todo cuelga de /api/catalogos. Son listas publicas: no piden token.

Pantallas que las usan: 1a (centrar el mapa), 1c (poblar los nueve filtros),
1e y 1j (selectores de los dos perfiles).
"""

from fastapi import APIRouter
from sqlalchemy import select

from app.dependencias import Db
from app.modulos.catalogos import esquemas, logica, modelos

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/todo", response_model=esquemas.CatalogoCompletoOut)
def catalogo_completo(db: Db):
    """Materias, etapas, barrios, centros e idiomas en un solo llamado.
    El frontend lo pide una vez al entrar y lo
    cachea; estas listas casi no cambian.
    """
    return {
        "materias": listar_materias(db),
        "etapas": listar_etapas(db),
        "barrios": listar_barrios(db),
        "centros": listar_centros(db),
        "idiomas": listar_idiomas(db),
    }


@router.get("/barrios", response_model=list[esquemas.BarrioOut])
def listar_barrios(db: Db):
    """Devolver todos los barrios ordenados por nombre."""
    #SELECT * FROM barrio ORDER BY nombre;
    consulta = select(modelos.Barrio).order_by(modelos.Barrio.nombre)
    return list(db.scalars(consulta).all())


@router.get("/materias", response_model=list[esquemas.MateriaOut])
def listar_materias(db: Db):
    """Materias activas, ordenadas por nombre.Filtrar por activa = true"""
    consulta = (
        select(modelos.Materia)
        .where(modelos.Materia.activa.is_(True))
        .order_by(modelos.Materia.nombre)
    )
    return list(db.scalars(consulta).all())


@router.get("/etapas", response_model=list[esquemas.EtapaOut])
def listar_etapas(db: Db):
    """Etapas educativas ordenadas por la columna `orden`"""
    consulta = select(modelos.EtapaEducativa).order_by(modelos.EtapaEducativa.orden)
    return list(db.scalars(consulta).all())


@router.get("/centros", response_model=list[esquemas.CentroOut])
def listar_centros(db: Db, barrio_id: int | None = None):
    """Centros educativos, opcionalmente filtrados por barrio."""
    if barrio_id is not None:
        consulta = (
            select(modelos.CentroEducativo)
            .where(modelos.CentroEducativo.barrio_id == barrio_id)
            .order_by(modelos.CentroEducativo.nombre)
        )
    else:
        consulta = select(modelos.CentroEducativo).order_by(modelos.CentroEducativo.nombre)
    return list(db.scalars(consulta).all())


@router.get("/idiomas", response_model=list[esquemas.IdiomaOut])
def listar_idiomas(db: Db):
    """Idiomas en los que se puede dictar"""
    consulta = select(modelos.Idioma).order_by(modelos.Idioma.nombre)
    return list(db.scalars(consulta).all())


@router.get("/parametros", response_model=esquemas.ParametrosOut)
def parametros(db: Db):
    """Comision de servicio y tasa de IVA vigentes.
    No lo pide ninguna pantalla directamente (el desglose siempre viene armado
    de POST /clases/cotizar), pero es util para depurar y para la defensa.
    """
    return logica.parametros_vigentes(db)
