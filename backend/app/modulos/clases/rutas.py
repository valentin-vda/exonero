"""Rutas HTTP del modulo clases - dueno P4.

Todo cuelga de /api/clases.

OJO CON EL ORDEN DE LAS RUTAS: las literales (/proxima, /pendientes,
/metricas, /series, /mis-profesores, /mis-alumnos, /cotizar) van ANTES que
/{clase_id}, o FastAPI intenta interpretar "proxima" como un id y devuelve 422.

Las rutas de un solo rol usan `Estudiante` o `Profesor` (ver
app/dependencias.py): con el otro rol, 403 no_es_tuyo. Las que sirven a los
dos (el calendario, la proxima, cancelar, reprogramar) usan `Yo`.

Igual que en P1: cada ruta llama a logica.py, hace el commit y responde.
"""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Query, Response, status

from app import fechas
from app.dependencias import Db, Estudiante, Profesor, Yo
from app.modulos.clases import esquemas, logica

router = APIRouter(prefix="/clases", tags=["clases"])


# ============================================================================
# Rutas literales - van primero
# ============================================================================

@router.post("/cotizar", response_model=esquemas.CotizacionOut)
def cotizar(datos: esquemas.CotizarIn, db: Db):
    """El desglose del importe. Compartido por 1f y 1g.

    EL MAS PELIGROSO DE DUPLICAR: el estimado de la ficha y el detalle del
    checkout tienen que salir del mismo calculo.

    No crea nada. No pide token: el alumno ve el estimado en 1f antes de entrar.

    Errores: 400 modalidad_invalida, 404 profesor_no_existe,
             400 duracion_invalida, 400 sin_precio.
    """
    return logica.cotizar(db, datos.profesor_id, datos.duracion_min, datos.modalidad, datos.con_traslado)


@router.get(
    "/proxima",
    response_model=esquemas.ProximaClaseOut,
    responses={204: {"description": "No hay ninguna clase aprobada por delante"}},
)
def proxima_clase(yo: Yo, db: Db):
    """La siguiente clase aprobada, con cuenta regresiva. 1a, 1b y 1d.

    El recordatorio del alumno y el del profesor son el mismo dato desde dos
    lados. Para el profesor, la contraparte trae ademas etapa, centro y
    telefono del alumno: asi 1d no necesita un segundo llamado.

    Devuelve 204 sin contenido si no hay ninguna aprobada por delante (el
    frontend recibe null, ver api/cliente.js).
    """
    clase = logica.proxima(db, yo.id)
    if clase is None:
        # Una Response devuelta tal cual se saltea response_model: 204 sin cuerpo.
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return clase


@router.get("/pendientes", response_model=list[esquemas.SolicitudOut])
def solicitudes_pendientes(yo: Profesor, db: Db):
    """Las solicitudes por aprobar. 1i.

    Sin expiracion automatica: quedan pendientes hasta que el profesor responda.
    El importe ya viene congelado en la clase, no se vuelve a cotizar.
    """
    return logica.solicitudes_pendientes(db, yo.id)


@router.get("/metricas", response_model=esquemas.MetricasOut)
def metricas(yo: Profesor, db: Db, periodo: str = "mes"):
    """Los cinco indicadores de 1d: alumnos atendidos, horas dictadas, alumnos
    recurrentes, tasa de cancelacion y la variacion contra el periodo anterior.

    periodo: mes, trimestre o anio, el calendario en curso contra el anterior
    del mismo largo. Las definiciones estan en logica.metricas().

    Error: 400 periodo_invalido.
    """
    return logica.metricas(db, yo.id, periodo)


@router.get("/series", response_model=list[esquemas.PuntoSerie])
def series(yo: Profesor, db: Db, agrupar: str = "semana"):
    """El grafico de reservas de 1d: cantidad de clases por punto, separadas
    por estado. agrupar: semana, mes o anio (ultimas 10 semanas, 12 meses o
    5 anios, incluido el actual).

    Agrupa con date_trunc de PostgreSQL, en la zona de Montevideo.
    Error: 400 agrupacion_invalida.
    """
    return logica.series(db, yo.id, agrupar)


@router.get("/mis-profesores", response_model=list[esquemas.PersonaConResena])
def mis_profesores(yo: Estudiante, db: Db):
    """Profesores con los que el alumno ya tuvo clase (dictada). 1b.

    Trae mi_resena adentro: la que este alumno ya dejo, o null. Con eso la
    pantalla sabe si mostrar el boton de resenar o la resena existente, sin
    hacer otra llamada.

    mi_resena sale de resenas.resena_de() (P3), y no de un LEFT JOIN con la
    tabla resena: clases no puede leer las tablas de otro modulo.
    """
    return logica.mis_profesores(db, yo.id)


@router.get("/mis-alumnos", response_model=list[esquemas.PersonaConResena])
def mis_alumnos(yo: Profesor, db: Db):
    """Lo mismo que mis-profesores pero del lado del profesor. 1i.

    Mismo contrato en los dos sentidos; materias y precio_hora solo aparecen
    cuando la persona es un profesor.
    """
    return logica.mis_alumnos(db, yo.id)


@router.get("", response_model=list[esquemas.ClaseOut])
def listar_clases(yo: Yo, db: Db, desde: date | None = None, hasta: date | None = None,
                  estado: str | None = None, pagina: int = Query(1, ge=1)):
    """El calendario. UNO SOLO para 1b, 1d y 1i. De a 50 por pagina, por inicio.

    El del alumno y el del profesor son la misma consulta: el rol sale del
    token y decide por que columna se filtra. Por eso 1d no necesita otro
    endpoint.

    desde y hasta son fechas (AAAA-MM-DD) de Montevideo; hasta es inclusive.
    Error: 400 estado_no_permitido si estado no es un estado de clase.
    """
    desde_dt, hasta_dt = fechas.rango_de_dias(desde, hasta)
    return logica.clases_entre(db, yo.id, desde_dt, hasta_dt, estado, pagina)


@router.post("", response_model=esquemas.ClaseCreadaOut, status_code=status.HTTP_201_CREATED)
def crear_clase(datos: esquemas.CrearClaseIn, yo: Estudiante, db: Db):
    """El confirmar de 1g. Crea la clase en pendiente y retiene el cobro.

    Aparece enseguida en las solicitudes del profesor (1i).

    Un solo commit para la clase y el cobro: si la tarjeta falla, logica
    levanta el error antes de llegar aca y no queda ninguna de las dos cosas.

    Errores: los de cotizar, 400 materia_no_existe, 409 horario_ocupado,
             404 tarjeta_no_existe, 402 tarjeta_vencida, 402 cobro_rechazado.
    """
    clase = logica.crear(db, yo.id, datos)
    respuesta = logica.resumen(db, clase)
    db.commit()
    return respuesta


# ============================================================================
# Rutas con id - van al final
# ============================================================================

@router.post("/{clase_id}/aprobar", response_model=esquemas.ClaseCreadaOut)
def aprobar_clase(clase_id: int, yo: Profesor, db: Db):
    """El profesor acepta la solicitud. 1i.

    La clase pasa a aprobada, el cobro a cobrado y el horario queda ocupado.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido,
    409 horario_ocupado (se aprobo otra encima mientras tanto: lo detecta la
    restriccion EXCLUDE de la base).
    """
    clase = logica.aprobar(db, clase_id, yo.id)
    respuesta = logica.resumen(db, clase)
    db.commit()
    return respuesta


@router.delete("/{clase_id}", status_code=status.HTTP_204_NO_CONTENT)
def rechazar_clase(clase_id: int, yo: Profesor, db: Db):
    """El profesor rechaza. BORRA la fila y libera el cobro retenido. 1i.

    La clase rechazada no deja rastro; el cobro liberado si (aparece en el
    historial del alumno).

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido.
    """
    logica.rechazar(db, clase_id, yo.id)
    db.commit()
    return None


@router.post("/{clase_id}/cancelar", response_model=esquemas.CancelarOut)
def cancelar_clase(clase_id: int, datos: esquemas.CancelarIn, yo: Yo, db: Db,
                   tareas: BackgroundTasks):
    """Cancela una clase pendiente o aprobada. Compartido por 1b y 1i.

    Las dos partes pueden cancelar; quien lo hizo sale del token. NO borra:
    pasa a cancelada y queda en el historial.

    Si estaba pendiente, la plata retenida se libera en el momento
    (reembolso.estado = "liberado"). Si estaba aprobada, el reembolso corre en
    BackgroundTask: la respuesta vuelve al instante con "en_proceso" y el
    cobro pasa a reembolsado unos segundos despues. La tarea corre despues
    de este commit, asi que ya ve la clase cancelada.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido.
    """
    respuesta = logica.cancelar(db, clase_id, yo.id, datos.motivo, tareas)
    db.commit()
    return respuesta


@router.post("/{clase_id}/reprogramar", response_model=esquemas.ClaseOut)
def reprogramar_clase(clase_id: int, datos: esquemas.ReprogramarIn, yo: Yo, db: Db):
    """Mueve la clase de horario. Compartido por 1b y 1i.

    Vuelve a estado pendiente: el profesor la tiene que aprobar otra vez. Los
    importes no cambian. Devuelve la clase como una fila del calendario.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido,
    400 duracion_no_modificable, 409 horario_ocupado.
    """
    clase = logica.reprogramar(db, clase_id, yo.id, datos.inicio, datos.duracion_min)
    db.commit()
    return logica.armar_clases(db, [clase], yo.id)[0]


@router.post("/{clase_id}/completar", response_model=esquemas.ClaseOut)
def completar_clase(clase_id: int, datos: esquemas.CompletarIn, yo: Profesor, db: Db):
    """El profesor la marca como dictada o no_asistida. 1i.

    Suma a las clases dictadas del profesor y habilita resenar al alumno.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 400 estado_no_permitido,
    409 estado_invalido (no estaba aprobada).
    """
    clase = logica.completar(db, clase_id, yo.id, datos.estado)
    db.commit()
    return logica.armar_clases(db, [clase], yo.id)[0]
