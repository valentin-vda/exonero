"""Contratos de entrada y salida del modulo pagos."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TarjetaIn(BaseModel):
    """POST /pagos/tarjetas - 1e y 1g."""

    numero: str = Field(min_length=13, max_length=19)
    titular: str
    vence_mes: int = Field(ge=1, le=12)
    vence_anio: int
    ccv: str = Field(min_length=3, max_length=4)


class TarjetaOut(BaseModel):
    """Lo que se devuelve de una tarjeta.

    NUNCA el numero completo ni el CCV, aunque esten guardados. La marca se
    deduce del primer digito y ultimos4 son los ultimos cuatro: con eso alcanza
    para que el alumno reconozca cual es.
    """

    id: int
    marca: str        # Visa, Mastercard, OCA, Otra
    ultimos4: str
    titular: str
    vence: str        # MM/AA


class MovimientoOut(BaseModel):
    """Una fila del historial de pagos de 1e. Incluye los reembolsos."""

    id: int
    fecha: datetime
    clase_id: int
    materia: str | None = None
    contraparte: str | None = None
    importe: Decimal
    estado: str


class IngresosOut(BaseModel):
    """GET /pagos/ingresos - compartido por 1d y 1j.

    cobrado    suma de los cobros en estado cobrado
    pendiente  lo retenido, todavia sin aprobar
    """

    cobrado: Decimal
    pendiente: Decimal
    promedio_por_clase: Decimal
    serie: list[dict] = []


class OkOut(BaseModel):
    ok: bool = True
