"""Rutas HTTP del modulo agenda - dueno P3.

Todo cuelga de /api/agenda. Dos familias:
  /agenda/profesores/{id}/...  lo que ve el alumno (publico)
  /agenda/yo/...               lo que edita el profesor (con token, rol profesor)

Igual que en el resto: cada ruta llama a logica.py, hace el commit y responde.
"""

from datetime import date

from fastapi import APIRouter, Query, Response, status

from app import fechas
from app.dependencias import Db, Profesor
from app.errores import ErrorAPI
from app.modulos.agenda import esquemas, logica

router = APIRouter(prefix="/agenda", tags=["agenda"])


@router.get("/profesores/{profesor_id}/disponibilidad", response_model=list[esquemas.DiaConHuecos])
def disponibilidad(
    profesor_id: int,
    db: Db,
    desde: date,
    hasta: date,
    duracion: int = Query(60, ge=15, le=480),
):
    """Los huecos libres de un profesor. Compartido por 1c, 1f y 1i.

    El calendario que ve el alumno y el que ve el profesor leen exactamente lo
    mismo: un solo endpoint, una sola definicion de "libre".

    Ya vienen descontados clases aprobadas, bloqueos, descanso entre clases,
    tope de clases por dia y aviso minimo. El frontend solo los dibuja.

    `profesor_id` es el usuario.id. `hasta` es inclusive.
    Errores: 400 rango_invalido (hasta antes que desde, o mas de 31 dias),
    404 profesor_no_existe.
    """
    if hasta < desde or (hasta - desde).days >= logica.MAX_DIAS_RANGO:
        raise ErrorAPI(400, "rango_invalido")
    return logica.huecos_libres(db, profesor_id, desde, hasta, duracion)


@router.post("/verificar", response_model=esquemas.VerificarOut)
def verificar_horario(datos: esquemas.VerificarIn, db: Db):
    """Dice si un horario sigue libre. Compartido por 1f, 1g y 1i.

    Se llama dos veces en el flujo de reserva: al elegir el horario y al
    confirmar. No reserva nada: solo consulta.

    Error: 404 profesor_no_existe.
    """
    return logica.verificar(db, datos.profesor_id, datos.inicio, datos.duracion_min)


@router.get("/yo/semana", response_model=esquemas.SemanaOut)
def semana_del_profesor(yo: Profesor, db: Db, desde: date | None = None):
    """El calendario semanal de 1i: aprobadas, pendientes, cerradas y bloqueos.

    En una sola respuesta para no hacer varias llamadas y cruzarlas en el
    frontend. Son siete dias desde `desde` (por defecto, hoy).
    """
    perfil = logica.perfil_propio(db, yo.id)
    return logica.semana(db, perfil, desde or fechas.ahora().date())


@router.get("/yo/franjas", response_model=list[esquemas.FranjaOut])
def listar_franjas(yo: Profesor, db: Db):
    """Las franjas semanales del profesor. Compartido por 1i y 1j.

    La disponibilidad se edita desde la agenda y desde el perfil: es la misma
    pantalla embebida dos veces, no se duplica el endpoint.
    """
    return logica.franjas_de(db, logica.perfil_propio(db, yo.id).id)


@router.put("/yo/franjas", response_model=list[esquemas.FranjaOut])
def guardar_franjas(datos: esquemas.FranjasIn, yo: Profesor, db: Db):
    """Reemplaza TODAS las franjas del profesor por las que vienen.

    Achicar la disponibilidad NO cancela clases ya aprobadas: quedan como
    estan. La pantalla lo avisa.

    Errores: 400 franja_invalida, 409 franjas_superpuestas.
    """
    perfil = logica.perfil_propio(db, yo.id)
    franjas = logica.reemplazar_franjas(db, perfil.id, datos.franjas)
    db.commit()
    return franjas


@router.get("/yo/bloqueos", response_model=list[esquemas.BloqueoOut])
def listar_bloqueos(yo: Profesor, db: Db, desde: date | None = None, hasta: date | None = None):
    """Los bloqueos del profesor en un rango. Sin rango, los que no terminaron."""
    perfil = logica.perfil_propio(db, yo.id)
    inicio, fin = fechas.rango_de_dias(desde, hasta)
    return logica.bloqueos_entre(db, perfil.id, inicio, fin)


@router.post("/yo/bloqueos", response_model=esquemas.BloqueoOut, status_code=status.HTTP_201_CREATED)
def crear_bloqueo(datos: esquemas.BloqueoIn, yo: Profesor, db: Db):
    """Bloquea un rato puntual.

    Errores: 400 bloqueo_invalido, 409 hay_clase_aprobada (primero hay que
    cancelarla o reprogramarla), 409 bloqueo_superpuesto.
    """
    perfil = logica.perfil_propio(db, yo.id)
    bloqueo = logica.crear_bloqueo(db, perfil, datos)
    db.commit()
    return bloqueo


@router.delete("/yo/bloqueos/{bloqueo_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_bloqueo(bloqueo_id: int, yo: Profesor, db: Db):
    """Saca un bloqueo y devuelve ese rato a la disponibilidad.

    Errores: 404 bloqueo_no_existe, 403 no_es_tuyo.
    """
    perfil = logica.perfil_propio(db, yo.id)
    logica.borrar_bloqueo(db, perfil.id, bloqueo_id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
