"""Contratos de entrada y salida del modulo clases.

Copiados de la seccion 9 de la spec. El mas delicado es CotizacionOut: el
estimado de la ficha (1f) y el detalle del checkout (1g) tienen que salir del
mismo calculo, o los dos numeros van a diferir y nadie va a saber cual vale.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


# --- Cotizar ----------------------------------------------------------------

class CotizarIn(BaseModel):
    """POST /clases/cotizar - 1f y 1g."""

    profesor_id: int
    duracion_min: int
    modalidad: str
    con_traslado: bool = False


class CotizacionOut(BaseModel):
    """El desglose completo. No crea nada: es solo el calculo.

    Orden del calculo:
      subtotal  = precio_hora * horas
      comision  = (subtotal + traslado) * pct_comision / 100
      impuesto  = (subtotal + traslado + comision) * pct_iva / 100
      total     = subtotal + traslado + comision + impuesto
    """

    precio_hora: Decimal
    horas: Decimal
    subtotal: Decimal
    costo_traslado: Decimal
    pct_comision: Decimal
    comision: Decimal
    pct_iva: Decimal
    impuesto: Decimal
    total: Decimal


# --- Crear ------------------------------------------------------------------

class CrearClaseIn(BaseModel):
    """POST /clases - el confirmar de 1g."""

    profesor_id: int
    materia_id: int
    etapa_id: int | None = None
    tema: str | None = None
    inicio: datetime
    duracion_min: int
    modalidad: str
    con_traslado: bool = False
    tarjeta_id: int


class CobroEnClase(BaseModel):
    estado: str


class ClaseCreadaOut(BaseModel):
    id: int
    estado: str
    total: Decimal
    cobro: CobroEnClase


# --- Lectura ----------------------------------------------------------------

class Contraparte(BaseModel):
    """La otra persona de la clase.

    Es el profesor si mira el alumno, y el alumno si mira el profesor. El rol
    sale del token, y por eso 1d no necesita otro endpoint distinto de 1b.
    """

    id: int
    nombre: str
    apellido: str | None = None
    foto_base64: str | None = None
    etapa: str | None = None
    centro: str | None = None
    telefono: str | None = None
    puntaje_promedio: Decimal | None = None
    cantidad_resenas: int | None = None


class ClaseOut(BaseModel):
    """Una fila del calendario. GET /clases - 1b, 1d, 1i."""

    id: int
    estado: str
    inicio: datetime
    duracion_min: int
    materia: str | None = None
    tema: str | None = None
    modalidad: str
    ubicacion: str | None = None
    total: Decimal
    cobro_estado: str | None = None
    contraparte: Contraparte


class ProximaClaseOut(ClaseOut):
    """GET /clases/proxima - 1a, 1b, 1d. Agrega la cuenta regresiva."""

    minutos_restantes: int


class SolicitudOut(BaseModel):
    """GET /clases/pendientes - 1i.

    El importe YA esta congelado en la clase: no se vuelve a cotizar.
    """

    id: int
    inicio: datetime
    duracion_min: int
    materia: str | None = None
    tema: str | None = None
    total: Decimal
    solicitada_el: datetime
    alumno: Contraparte


class PersonaConResena(BaseModel):
    """GET /clases/mis-profesores y /mis-alumnos - 1b y 1i.

    mi_resena viene en null si todavia no dejo ninguna: con eso la pantalla
    decide si muestra el boton de resenar o la resena que ya escribio.
    """

    persona: dict
    cantidad_clases: int
    ultima_clase: datetime | None = None
    mi_resena: dict | None = None


# --- Acciones ---------------------------------------------------------------

class CancelarIn(BaseModel):
    motivo: str | None = None


class CancelarOut(BaseModel):
    id: int
    estado: str
    cancelada_por: str
    reembolso: dict


class ReprogramarIn(BaseModel):
    inicio: datetime
    duracion_min: int | None = None


class CompletarIn(BaseModel):
    """POST /clases/{id}/completar - dictada o no_asistida."""

    estado: str = "dictada"


# --- Panel del profesor - 1d ------------------------------------------------

class MetricasOut(BaseModel):
    """Los cinco indicadores de 1d, con la variacion contra el periodo anterior."""

    alumnos_atendidos: int
    horas_dictadas: Decimal
    alumnos_recurrentes: int
    tasa_cancelacion: Decimal
    variacion: dict


class PuntoSerie(BaseModel):
    etiqueta: str
    cantidad: int
    estado: str | None = None
