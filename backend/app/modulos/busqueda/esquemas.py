"""Contratos de entrada y salida del modulo busqueda."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FiltrosBusqueda(BaseModel):
    """Los nueve filtros combinables de 1c, mas orden y pagina.

    No se guardan: se pierden al salir de la pantalla (decision de la spec).
    Todos opcionales; los que no vienen no filtran.
    """

    materia: int | None = None
    etapa: int | None = None
    centro: int | None = None
    precio_min: Decimal | None = None
    precio_max: Decimal | None = None
    barrio: int | None = None
    modalidad: str | None = None
    puntaje_min: Decimal | None = None
    dia: int | None = None          # 0 a 6, para el filtro de disponibilidad
    franja: str | None = None       # manana, tarde, noche, fin_de_semana
    idioma: int | None = None
    orden: str = "distancia"        # distancia, puntaje, precio
    pagina: int = 1


class ResultadoBusqueda(BaseModel):
    """Una fila de la tabla de resultados de 1c."""

    id: int
    nombre: str
    apellido: str
    foto_base64: str | None = None
    materias: list[str] = []
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
    resultados: list[ResultadoBusqueda] = []


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
    materias: list[str] = []
    barrio: str | None = None
    distancia_km: float | None = None
    modalidad: str
    precio_hora: Decimal | None = None
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0
    primera_hora_libre: datetime | None = None
