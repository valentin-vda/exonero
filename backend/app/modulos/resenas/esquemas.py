"""Contratos de entrada y salida del modulo resenas.

Fijate que en NINGUN esquema de salida aparece el autor. Es a proposito: ni el
id, ni el nombre, ni nada que permita deducir quien la escribio.
"""

from datetime import date

from pydantic import BaseModel, Field


class ResenaIn(BaseModel):
    """POST y PUT /resenas - 1b y 1i.

    El sentido NO viene en el cuerpo: sale del rol del token. Asi nadie puede
    falsear que un profesor lo reseno.
    """

    destinatario_id: int
    puntaje: int = Field(ge=1, le=5)
    texto: str | None = Field(None, max_length=500)


class ResenaOut(BaseModel):
    """Una resena, sin autor."""

    puntaje: int
    texto: str | None = None
    fecha: date


class ResumenResenasOut(BaseModel):
    """GET /resenas/resumen/{usuario_id} - 1d, 1e, 1f, 1i, 1j.

    El mismo contrato sirve para un profesor y para un alumno.

    distribucion es cuantas resenas de cada estrella: {"5": 24, "4": 6, ...}
    Es lo que dibuja el grafico de barras de 1f.
    """

    total: int
    promedio: float
    distribucion: dict[str, int]


class PaginaResenasOut(ResumenResenasOut):
    """GET /resenas/usuario/{id} - agrega la lista paginada."""

    resenas: list[ResenaOut] = []
