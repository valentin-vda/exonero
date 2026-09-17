"""Contratos de entrada y salida del modulo mensajeria."""

from datetime import datetime

from pydantic import BaseModel


class ContraparteHilo(BaseModel):
    """La otra persona de la conversacion."""

    id: int
    nombre: str
    apellido: str | None = None
    foto_base64: str | None = None
    materias: list[str] = []


class HiloOut(BaseModel):
    """Una fila de la bandeja de 1h, ordenada por ultimo_mensaje_el."""

    id: int
    contraparte: ContraparteHilo
    ultimo_mensaje: str | None = None
    ultimo_mensaje_el: datetime | None = None
    no_leidos: int = 0


class AbrirHiloIn(BaseModel):
    """POST /mensajes/hilos - el boton de contactar de 1f.

    Devuelve el hilo existente si ya lo hay; no crea uno nuevo cada vez.
    """

    profesor_id: int


class MensajeOut(BaseModel):
    id: int
    autor_id: int
    contenido: str
    enviado_el: datetime


class EnviarMensajeIn(BaseModel):
    """Las respuestas rapidas son texto predefinido del frontend: llegan por
    aca como un mensaje comun."""

    texto: str


class NoLeidosOut(BaseModel):
    """GET /mensajes/no-leidos - lo consultan LAS DIEZ PANTALLAS cada diez
    segundos, porque vive en la cabecera."""

    no_leidos: int
