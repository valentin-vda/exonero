"""Rutas HTTP del modulo clases - dueno P4.

Todo cuelga de /api/clases.

OJO CON EL ORDEN DE LAS RUTAS: las literales (/proxima, /pendientes,
/metricas, /series, /mis-profesores, /mis-alumnos, /cotizar) van ANTES que
/{clase_id}, o FastAPI intenta interpretar "proxima" como un id y devuelve 422.
"""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Response, status

from app.dependencias import Db, Yo
from app.modulos.clases import esquemas

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

    TODO (P4): implementar. Envolver logica.cotizar().
    """
    raise NotImplementedError("P4 - clases: POST /clases/cotizar")


@router.get("/proxima")
def proxima_clase(yo: Yo, db: Db, respuesta: Response):
    """La siguiente clase aprobada, con cuenta regresiva. 1a, 1b y 1d.

    El recordatorio del alumno y el del profesor son el mismo dato desde dos
    lados. Para el profesor, la contraparte trae ademas etapa, centro y
    telefono del alumno: asi 1d no necesita un segundo llamado.

    Devuelve 204 sin contenido si no hay ninguna aprobada por delante.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: GET /clases/proxima")


@router.get("/pendientes", response_model=list[esquemas.SolicitudOut])
def solicitudes_pendientes(yo: Yo, db: Db):
    """Las solicitudes por aprobar. 1i.

    Sin expiracion automatica: quedan pendientes hasta que el profesor responda.
    El importe ya viene congelado en la clase, no se vuelve a cotizar.

    TODO (P4): implementar. 403 si el rol no es profesor.
    """
    raise NotImplementedError("P4 - clases: GET /clases/pendientes")


@router.get("/metricas", response_model=esquemas.MetricasOut)
def metricas(yo: Yo, db: Db, periodo: str = "mes"):
    """Los cinco indicadores de 1d: alumnos atendidos, horas dictadas, alumnos
    recurrentes, tasa de cancelacion y la variacion contra el periodo anterior.

    periodo: mes, trimestre o anio.

    TODO (P4): implementar.
      alumnos_atendidos   distintos estudiante_id con clase dictada
      horas_dictadas      suma de duracion_min / 60 de las dictadas
      alumnos_recurrentes los que tuvieron 2 o mas clases dictadas
      tasa_cancelacion    canceladas sobre canceladas mas dictadas
      variacion           lo mismo para el periodo anterior, en porcentaje
    """
    raise NotImplementedError("P4 - clases: GET /clases/metricas")


@router.get("/series", response_model=list[esquemas.PuntoSerie])
def series(yo: Yo, db: Db, agrupar: str = "semana"):
    """El grafico de reservas de 1d: cantidad de clases por punto, separadas
    por estado. agrupar: semana, mes o anio.

    TODO (P4): implementar. Usar date_trunc de PostgreSQL para agrupar.
    """
    raise NotImplementedError("P4 - clases: GET /clases/series")


@router.get("/mis-profesores", response_model=list[esquemas.PersonaConResena])
def mis_profesores(yo: Yo, db: Db):
    """Profesores con los que el alumno ya tuvo clase. 1b.

    Trae mi_resena adentro: la que este alumno ya dejo, o null. Con eso la
    pantalla sabe si mostrar el boton de resenar o la resena existente, sin
    hacer otra llamada.

    TODO (P4): implementar. El LEFT JOIN con resena sobre
    (autor_id = yo, destinatario_id = profesor) resuelve mi_resena en la misma
    consulta, gracias al UNIQUE (autor_id, destinatario_id).
    """
    raise NotImplementedError("P4 - clases: GET /clases/mis-profesores")


@router.get("/mis-alumnos", response_model=list[esquemas.PersonaConResena])
def mis_alumnos(yo: Yo, db: Db):
    """Lo mismo que mis-profesores pero del lado del profesor. 1i.

    Mismo contrato en los dos sentidos; materias y precio_hora solo aparecen
    cuando la persona es un profesor.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: GET /clases/mis-alumnos")


@router.get("", response_model=list[esquemas.ClaseOut])
def listar_clases(yo: Yo, db: Db, desde: date | None = None, hasta: date | None = None,
                  estado: str | None = None, pagina: int = 1):
    """El calendario. UNO SOLO para 1b, 1d y 1i.

    El del alumno y el del profesor son la misma consulta: el rol sale del
    token y decide por que columna se filtra. Por eso 1d no necesita otro
    endpoint.

    TODO (P4): implementar. Envolver logica.clases_entre().
    """
    raise NotImplementedError("P4 - clases: GET /clases")


@router.post("", response_model=esquemas.ClaseCreadaOut, status_code=status.HTTP_201_CREATED)
def crear_clase(datos: esquemas.CrearClaseIn, yo: Yo, db: Db):
    """El confirmar de 1g. Crea la clase en pendiente y retiene el cobro.

    Aparece enseguida en las solicitudes del profesor (1i).

    Errores: 409 horario_ocupado, 402 cobro_rechazado.

    TODO (P4): implementar. 403 si el rol no es estudiante.
    """
    raise NotImplementedError("P4 - clases: POST /clases")


# ============================================================================
# Rutas con id - van al final
# ============================================================================

@router.post("/{clase_id}/aprobar", response_model=esquemas.ClaseCreadaOut)
def aprobar_clase(clase_id: int, yo: Yo, db: Db):
    """El profesor acepta la solicitud. 1i.

    La clase pasa a aprobada, el cobro a cobrado y el horario queda ocupado.

    TODO (P4): implementar. 409 horario_ocupado si se aprobo otra encima
    mientras tanto: lo detecta la restriccion EXCLUDE de la base.
    """
    raise NotImplementedError("P4 - clases: POST /clases/{id}/aprobar")


@router.delete("/{clase_id}", status_code=status.HTTP_204_NO_CONTENT)
def rechazar_clase(clase_id: int, yo: Yo, db: Db):
    """El profesor rechaza. BORRA la fila y libera el cobro retenido. 1i.

    La clase rechazada no deja rastro.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: DELETE /clases/{id}")


@router.post("/{clase_id}/cancelar", response_model=esquemas.CancelarOut)
def cancelar_clase(clase_id: int, datos: esquemas.CancelarIn, yo: Yo, db: Db,
                   tareas: BackgroundTasks):
    """Cancela una clase aprobada. Compartido por 1b y 1i.

    Las dos partes pueden cancelar; quien lo hizo sale del token. NO borra:
    pasa a cancelada y queda en el historial.

    El reembolso corre en BackgroundTask: la respuesta vuelve al instante y el
    cobro pasa a reembolsado unos segundos despues.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: POST /clases/{id}/cancelar")


@router.post("/{clase_id}/reprogramar", response_model=esquemas.ClaseOut)
def reprogramar_clase(clase_id: int, datos: esquemas.ReprogramarIn, yo: Yo, db: Db):
    """Mueve la clase de horario. Compartido por 1b y 1i.

    Vuelve a estado pendiente: el profesor la tiene que aprobar otra vez.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: POST /clases/{id}/reprogramar")


@router.post("/{clase_id}/completar", response_model=esquemas.ClaseOut)
def completar_clase(clase_id: int, datos: esquemas.CompletarIn, yo: Yo, db: Db):
    """El profesor la marca como dictada o no_asistida. 1i.

    Suma a las horas dictadas del profesor y habilita resenar al alumno.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: POST /clases/{id}/completar")
