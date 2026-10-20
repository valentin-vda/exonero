"""Rutas HTTP del modulo pagos - dueno P4.

Todo cuelga de /api/pagos.

Las tarjetas son el mismo recurso desde dos pantallas: el alta desde el
checkout (1g) y la administracion desde el perfil (1e). No se duplica.

Tarjetas e historial son solo del alumno (`Estudiante`) y los ingresos solo
del profesor (`Profesor`): con el otro rol, 403 no_es_tuyo.

Igual que en P1: cada ruta llama a logica.py, hace el commit y responde.
"""

from datetime import date

from fastapi import APIRouter, Query, status

from app import fechas
from app.dependencias import Db, Estudiante, Profesor
from app.modulos.pagos import esquemas, logica

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("/tarjetas", response_model=list[esquemas.TarjetaOut])
def listar_tarjetas(yo: Estudiante, db: Db):
    """Las tarjetas activas del alumno. Compartido por 1e y 1g.

    No hay tarjeta principal: el alumno elige una en cada compra.

    NUNCA devuelve el numero completo ni el CCV, aunque esten guardados: solo
    marca, ultimos4, titular y vence ("MM/AA").
    """
    return logica.tarjetas_de(db, yo.id)


@router.post("/tarjetas", response_model=esquemas.TarjetaOut, status_code=status.HTTP_201_CREATED)
def agregar_tarjeta(datos: esquemas.TarjetaIn, yo: Estudiante, db: Db):
    """Alta de tarjeta. Compartido por 1e y 1g.

    Se guarda tal cual, sin pasarela. Ver la advertencia de pagos/modelos.py.
    Devuelve la version segura, la misma forma que GET.

    Errores: 400 tarjeta_invalida (numero o CCV con algo que no son digitos;
             los espacios del numero se aceptan y se sacan),
             402 tarjeta_vencida.
    """
    tarjeta = logica.agregar_tarjeta(db, yo.id, datos)
    db.commit()
    return tarjeta


@router.delete("/tarjetas/{tarjeta_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_tarjeta(tarjeta_id: int, yo: Estudiante, db: Db):
    """Da de baja una tarjeta. Compartido por 1e y 1g.

    Baja LOGICA (activa = false), no DELETE: los cobros viejos apuntan a esta
    fila y el historial de 1e tiene que poder decir con que se pago.

    Errores: 404 tarjeta_no_existe, 403 no_es_tuyo (es de otro alumno).
    """
    logica.dar_de_baja_tarjeta(db, yo.id, tarjeta_id)
    db.commit()
    return None


@router.get("/historial", response_model=list[esquemas.MovimientoOut])
def historial(yo: Estudiante, db: Db, desde: date | None = None, hasta: date | None = None,
              pagina: int = Query(1, ge=1, le=1000)):
    """El historial de pagos del alumno. 1e. De a 50 por pagina.

    Son las filas de cobro de sus clases, con fecha, clase, importe y estado.
    Incluye los reembolsos de las canceladas y los liberados de las rechazadas
    (esos vienen con clase_id, materia y contraparte en null: la clase ya no
    existe).

    desde y hasta son fechas (AAAA-MM-DD) de Montevideo; hasta es inclusive.
    """
    desde_dt, hasta_dt = fechas.rango_de_dias(desde, hasta)
    return logica.historial_de(db, yo.id, desde_dt, hasta_dt, pagina)


@router.get("/ingresos", response_model=esquemas.IngresosOut)
def ingresos(yo: Profesor, db: Db, periodo: str = "mes", agrupar: str = "semana"):
    """Los ingresos del profesor. Compartido por 1d y 1j.

    El grafico del panel y el resumen del perfil salen del mismo endpoint.
    periodo: mes, trimestre o anio (el calendario en curso).
    agrupar: semana, mes o anio (los tramos de la serie del grafico).

    Errores: 400 periodo_invalido, 400 agrupacion_invalida.
    """
    return logica.ingresos_de(db, yo.id, periodo, agrupar)
