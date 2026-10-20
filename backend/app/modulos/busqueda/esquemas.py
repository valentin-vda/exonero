"""Contratos de entrada y salida del modulo busqueda."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class FiltrosBusqueda(BaseModel):
    """Los nueve filtros combinables de 1c, mas orden y pagina.

    No se guardan: se pierden al salir de la pantalla (decision de la spec).
    Todos opcionales; los que no vienen no filtran.
    """

    materia: int | None = Field(None, gt=0)
    etapa: int | None = Field(None, gt=0)
    centro: int | None = Field(None, gt=0)
    precio_min: Decimal | None = Field(None, ge=0)
    precio_max: Decimal | None = Field(None, ge=0)
    barrio: int | None = Field(None, gt=0)
    modalidad: Literal["presencial", "online", "ambas"] | None = None
    puntaje_min: Decimal | None = Field(None, ge=0, le=5)
    dia: int | None = Field(None, ge=0, le=6)
    franja: Literal["manana", "tarde", "noche", "fin_de_semana"] | None = None
    idioma: int | None = Field(None, gt=0)
    orden: Literal["distancia", "puntaje", "precio"] = "distancia"
    pagina: int = Field(1, ge=1, le=1000)


class ResultadoBusqueda(BaseModel):
    """Una fila de la tabla de resultados de 1c."""

    id: int
    nombre: str
    apellido: str
    foto_base64: str | None = None
    materias: list[str] = Field(default_factory=list)
    barrio: str | None = None
    modalidad: str
    precio_hora_presencial: Decimal | None = None
    precio_hora_online: Decimal | None = None
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0
    distancia_km: float | None = None
    proxima_hora_libre: datetime | None = None


class PaginaBusqueda(BaseModel):
    """Respuesta de GET /busqueda/profesores."""

    total: int
    pagina: int
    por_pagina: int = 20
    resultados: list[ResultadoBusqueda] = Field(default_factory=list)


class PinMapa(BaseModel):
    """Un pin de Leaflet. 1a, 1c y 1f consumen exactamente esto.

    El backend NO manda iconos, colores ni popups: solo coordenadas y los
    cuatro datos que el frontend escribe adentro del globito.
    """

    id: int
    nombre: str
    latitud: Decimal
    longitud: Decimal
    precio_hora: Decimal | None = None
    puntaje_promedio: Decimal = Decimal(0)
    modalidad: str


class ProfesorCercano(BaseModel):
    """Una tarjeta del carrusel de cercanos de 1a."""

    id: int
    nombre: str
    apellido: str
    foto_base64: str | None = None
    materias: list[str] = Field(default_factory=list)
    barrio: str | None = None
    distancia_km: float | None = None
    modalidad: str
    precio_hora: Decimal | None = None
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0
    primera_hora_libre: datetime | None = None
