"""Contratos de entrada y salida del modulo mensajeria."""

from datetime import datetime

from pydantic import BaseModel, Field


class ContraparteHilo(BaseModel):
    """La otra persona de la conversacion.

    Si es un profesor trae sus materias (para la cabecera del chat); si es un
    alumno, su etapa y su centro. Lo demas viene en null o vacio.
    """

    id: int
    nombre: str
    apellido: str | None = None
    foto_base64: str | None = None
    rol: str
    materias: list[str] = []
    etapa: str | None = None
    centro: str | None = None


class HiloOut(BaseModel):
    """Una fila de la bandeja de 1h, ordenada por ultimo_mensaje_el."""

    id: int
    contraparte: ContraparteHilo
    ultimo_mensaje: str | None = None
    ultimo_mensaje_el: datetime | None = None
    no_leidos: int = 0


class AbrirHiloIn(BaseModel):
    """POST /mensajes/hilos - el boton de contactar de 1f (y el "Mensaje" de 1a y 1d).

    Devuelve el hilo existente si ya lo hay; no crea uno nuevo cada vez.

    Se manda el id de la OTRA persona, en el campo de su rol:
      - el alumno manda profesor_id (como dice el contrato original)
      - el profesor manda estudiante_id (solo de un alumno con el que tenga clase)
    """

    profesor_id: int | None = None
    estudiante_id: int | None = None


class MensajeOut(BaseModel):
    id: int
    autor_id: int
    contenido: str
    enviado_el: datetime


class EnviarMensajeIn(BaseModel):
    """Las respuestas rapidas son texto predefinido del frontend: llegan por
    aca como un mensaje comun."""

    texto: str = Field(max_length=2000)


class NoLeidosOut(BaseModel):
    """GET /mensajes/no-leidos - lo consultan LAS DIEZ PANTALLAS cada diez
    segundos, porque vive en la cabecera."""

    no_leidos: int
