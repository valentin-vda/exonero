"""Rutas HTTP del modulo agenda - dueno P3.

Todo cuelga de /api/agenda. Dos familias:
  /agenda/profesores/{id}/...  lo que ve el alumno (publico)
  /agenda/yo/...               lo que edita el profesor (con token, rol profesor)
"""

from datetime import date

from fastapi import APIRouter, status

from app.dependencias import Db, Yo
from app.modulos.agenda import esquemas

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("/profesores/{profesor_id}/disponibilidad", response_model=list[esquemas.DiaConHuecos])
def disponibilidad(profesor_id: int, db: Db, desde: date, hasta: date, duracion: int = 60):
    """Los huecos libres de un profesor. Compartido por 1c, 1f y 1i.

    El calendario que ve el alumno y el que ve el profesor leen exactamente lo
    mismo: un solo endpoint, una sola definicion de "libre".

    Ya vienen descontados clases aprobadas, bloqueos, descanso entre clases,
    tope de clases por dia y aviso minimo. El frontend solo los dibuja.

    TODO (P3): implementar. Envolver logica.huecos_libres().
    """
    raise NotImplementedError("P3 - agenda: GET /agenda/profesores/{id}/disponibilidad")


@router.post("/verificar", response_model=esquemas.VerificarOut)
def verificar_horario(datos: esquemas.VerificarIn, db: Db):
    """Dice si un horario sigue libre. Compartido por 1f, 1g y 1i.

    Se llama dos veces en el flujo de reserva: al elegir el horario y al
    confirmar. No reserva nada: solo consulta.

    TODO (P3): implementar. Envolver logica.verificar().
    """
    raise NotImplementedError("P3 - agenda: POST /agenda/verificar")


@router.get("/yo/semana", response_model=esquemas.SemanaOut)
def semana_del_profesor(yo: Yo, db: Db, desde: date):
    """El calendario semanal de 1i: aprobadas, pendientes y bloqueos juntos.

    En una sola respuesta para no hacer tres llamadas y cruzarlas en el frontend.

    TODO (P3): implementar.
      1. 403 si el rol no es profesor.
      2. Pedirle las clases a clases.logica.clases_entre() y sumarle los bloqueos.
    """
    raise NotImplementedError("P3 - agenda: GET /agenda/yo/semana")


@router.get("/yo/franjas", response_model=list[esquemas.FranjaOut])
def listar_franjas(yo: Yo, db: Db):
    """Las franjas semanales del profesor. Compartido por 1i y 1j.

    La disponibilidad se edita desde la agenda y desde el perfil: es la misma
    pantalla embebida dos veces, no se duplica el endpoint.

    TODO (P3): implementar.
    """
    raise NotImplementedError("P3 - agenda: GET /agenda/yo/franjas")


@router.put("/yo/franjas", response_model=list[esquemas.FranjaOut])
def guardar_franjas(datos: esquemas.FranjasIn, yo: Yo, db: Db):
    """Reemplaza TODAS las franjas del profesor por las que vienen.

    TODO (P3): implementar.
      1. Validar cada franja: dia entre 0 y 6, hora_fin > hora_inicio.
      2. Rechazar franjas del mismo dia que se pisen entre si -> 409
         "franjas_superpuestas".
      3. Borrar las actuales e insertar las nuevas, en una sola transaccion.
      4. Achicar la disponibilidad NO cancela clases ya aprobadas: quedan como
         estan. Conviene avisarlo en la pantalla.
    """
    raise NotImplementedError("P3 - agenda: PUT /agenda/yo/franjas")


@router.get("/yo/bloqueos", response_model=list[esquemas.BloqueoOut])
def listar_bloqueos(yo: Yo, db: Db, desde: date | None = None, hasta: date | None = None):
    """Los bloqueos del profesor en un rango.

    TODO (P3): implementar.
    """
    raise NotImplementedError("P3 - agenda: GET /agenda/yo/bloqueos")


@router.post("/yo/bloqueos", response_model=esquemas.BloqueoOut, status_code=status.HTTP_201_CREATED)
def crear_bloqueo(datos: esquemas.BloqueoIn, yo: Yo, db: Db):
    """Bloquea un rato puntual.

    TODO (P3): implementar.
      1. fin > inicio -> 400 si no.
      2. NO se puede bloquear encima de una clase aprobada -> 409
         "hay_clase_aprobada". Primero hay que cancelarla o reprogramarla.
    """
    raise NotImplementedError("P3 - agenda: POST /agenda/yo/bloqueos")


@router.delete("/yo/bloqueos/{bloqueo_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_bloqueo(bloqueo_id: int, yo: Yo, db: Db):
    """Saca un bloqueo y devuelve ese rato a la disponibilidad.

    TODO (P3): implementar. 403 si el bloqueo no es de este profesor.
    """
    raise NotImplementedError("P3 - agenda: DELETE /agenda/yo/bloqueos/{id}")
