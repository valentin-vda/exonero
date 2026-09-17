"""Contratos de entrada y salida del modulo catalogos (Pydantic).

Estos modelos son lo que FastAPI serializa y lo que aparece en /docs. Van
aparte de modelos.py a proposito: modelos.py son las tablas, esquemas.py es
lo que viaja por HTTP. No son la misma cosa aunque se parezcan.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BarrioOut(BaseModel):
    """Lo que devuelve GET /catalogos/barrios. Leaflet usa lat/lon para centrar."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class MateriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nombre_corto: str | None = None


class EtapaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    orden: int
    niveles: list[str] | None = None


class CentroOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: str
    barrio_id: int | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class IdiomaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class CatalogoCompletoOut(BaseModel):
    """Respuesta de GET /catalogos/todo.

    Un solo llamado que llena todos los selectores de 1c, 1e y 1j. El frontend
    lo cachea: estas listas casi no cambian.
    """

    materias: list[MateriaOut]
    etapas: list[EtapaOut]
    barrios: list[BarrioOut]
    centros: list[CentroOut]
    idiomas: list[IdiomaOut]


class ParametrosOut(BaseModel):
    """Comision e IVA vigentes. No tiene ruta propia: lo consume clases por
    dentro, a traves de logica.parametros_vigentes()."""

    comision_servicio: Decimal
    tasa_iva: Decimal
