"""Contratos de entrada y salida del modulo agenda."""

from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Las filas del calendario semanal son las mismas de GET /clases: se reusa el
# contrato de clases en vez de copiarlo (y que los dos se desfasen).
from app.modulos.clases.esquemas import ClaseOut


class FranjaIn(BaseModel):
    """Una franja semanal, tal como la manda el editor de 1i y 1j."""

    dia_semana: int = Field(ge=0, le=6)   # 0 domingo ... 6 sabado
    hora_inicio: time
    hora_fin: time
    modalidad: Literal["presencial", "online", "ambas"] = "ambas"
    activa: bool = True


class FranjaOut(FranjaIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # En la tabla es un enum; aca sale como texto.
    modalidad: str


class FranjasIn(BaseModel):
    """PUT /agenda/yo/franjas manda TODAS las franjas juntas.

    Reemplazo completo en vez de altas y bajas sueltas: el editor es una grilla
    semanal, el usuario la deja como quiere y guarda una vez.
    """

    franjas: list[FranjaIn] = []


class BloqueoIn(BaseModel):
    inicio: datetime
    fin: datetime
    motivo: str | None = Field(None, max_length=200)


class BloqueoOut(BloqueoIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Hueco(BaseModel):
    """Un rato libre concreto, ya listo para dibujar."""

    inicio: datetime
    fin: datetime


class DiaConHuecos(BaseModel):
    """Los huecos de un dia. Es lo que dibuja el calendario de 1f."""

    fecha: str          # AAAA-MM-DD
    huecos: list[Hueco] = []


class VerificarIn(BaseModel):
    """POST /agenda/verificar - 1f, 1g, 1i."""

    profesor_id: int
    inicio: datetime
    duracion_min: int = Field(ge=15, le=480)


class VerificarOut(BaseModel):
    """La respuesta trae el motivo para que el frontend diga algo util.

    motivo, cuando libre es False:
      ocupado          ya hay una clase aprobada encima
      bloqueado        cae adentro de un bloqueo
      fuera_de_franja  ese dia y esa hora no estan en la disponibilidad
      aviso_minimo     es muy sobre la hora
      tope_diario      ese dia ya llego al maximo de clases
    """

    libre: bool
    motivo: str | None = None


class SemanaOut(BaseModel):
    """GET /agenda/yo/semana - el calendario de 1i en una sola respuesta.

    Trae aprobadas, pendientes, cerradas (dictadas y no asistidas) y bloqueos
    juntos, para no hacer varias llamadas y tener que cruzarlas en el frontend.
    Las clases tienen la misma forma que GET /clases.
    """

    desde: str
    hasta: str
    aprobadas: list[ClaseOut] = []
    pendientes: list[ClaseOut] = []
    cerradas: list[ClaseOut] = []
    bloqueos: list[BloqueoOut] = []
