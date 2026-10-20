"""Fechas y periodos, siempre en la zona de la aplicacion (America/Montevideo).

La base guarda timestamptz, que por dentro es UTC. Pero "el mes", "la semana"
o "el 21 de octubre" son de Montevideo: una clase del 31 a las 22:00 de aca
ya es dia 1 en UTC, y si se cortara en UTC caeria en el mes que no es.

Lo usan clases (el calendario, las metricas y las series de 1d) y pagos (el
historial de 1e y los ingresos de 1d). Esta aca y no en uno de los dos porque
clases ya importa pagos: si pagos importara clases, Python entraria en una
importacion circular. Igual que enums.py, no tiene tablas.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, literal_column

from app.config import ajustes
from app.errores import ErrorAPI

ZONA = ZoneInfo(ajustes.ZONA_HORARIA)

# Los periodos de las metricas de 1d: el calendario en curso.
PERIODOS = ("mes", "trimestre", "anio")

# Las agrupaciones de los graficos de 1d: (unidad de date_trunc, cuantos
# tramos se muestran, incluido el actual). El grafico dice "10 semanas".
AGRUPACIONES = {
    "semana": ("week", 10),
    "mes": ("month", 12),
    "anio": ("year", 5),
}


def ahora() -> datetime:
    """El momento actual, con zona."""
    return datetime.now(ZONA)


def con_zona(momento: datetime) -> datetime:
    """Le pone la zona de Montevideo a un datetime que llego sin zona.

    El frontend deberia mandar siempre la zona ("2026-10-21T18:00:00-03:00"),
    pero si llega "2026-10-21T18:00:00" a secas, PostgreSQL la interpretaria
    en la zona de la sesion de la base, que no tiene por que ser esta.
    """
    if momento.tzinfo is None:
        return momento.replace(tzinfo=ZONA)
    return momento


def inicio_del_dia(dia: date) -> datetime:
    """El 21 de octubre a las 00:00 de Montevideo."""
    return datetime.combine(dia, time(0), ZONA)


def rango_de_dias(desde: date | None, hasta: date | None) -> tuple[datetime | None, datetime | None]:
    """Un rango de fechas sin hora -> [desde 00:00, hasta + 1 dia 00:00).

    `hasta` es INCLUSIVE: ?desde=2026-10-01&hasta=2026-10-31 trae todo octubre,
    incluido el 31 a la noche. Por eso el borde de arriba es el dia siguiente,
    abierto. Cualquiera de los dos puede faltar.
    """
    return (
        inicio_del_dia(desde) if desde else None,
        inicio_del_dia(hasta + timedelta(days=1)) if hasta else None,
    )


def rango_periodo(periodo: str, atras: int = 0) -> tuple[datetime, datetime]:
    """El periodo calendario en curso: [inicio, fin). 400 si no es uno de PERIODOS.

    `atras` cuenta periodos completos hacia atras, para comparar:
      rango_periodo("mes")           octubre entero
      rango_periodo("mes", atras=1)  septiembre entero
      rango_periodo("trimestre")     octubre a diciembre
      rango_periodo("anio", 1)       el anio pasado
    """
    if periodo not in PERIODOS:
        raise ErrorAPI(400, "periodo_invalido")
    hoy = ahora().date()
    if periodo == "anio":
        primero = date(hoy.year - atras, 1, 1)
        return inicio_del_dia(primero), inicio_del_dia(date(primero.year + 1, 1, 1))

    meses = 1 if periodo == "mes" else 3
    # El primer mes del periodo: el actual, o el primero del trimestre (1, 4, 7, 10).
    mes_inicial = hoy.month if periodo == "mes" else (hoy.month - 1) // 3 * 3 + 1
    primero = _sumar_meses(date(hoy.year, mes_inicial, 1), -meses * atras)
    return inicio_del_dia(primero), inicio_del_dia(_sumar_meses(primero, meses))


def ventana(agrupar: str) -> tuple[datetime, datetime, str]:
    """La ventana de los graficos de 1d: (desde, hasta, unidad de date_trunc).

    Son los ultimos N tramos INCLUIDO el actual, enteros: con "semana", desde
    el lunes de hace nueve semanas hasta el lunes que viene. 400 si `agrupar`
    no es una de AGRUPACIONES.
    """
    if agrupar not in AGRUPACIONES:
        raise ErrorAPI(400, "agrupacion_invalida")
    unidad, tramos = AGRUPACIONES[agrupar]
    hoy = ahora().date()
    if agrupar == "semana":
        lunes = hoy - timedelta(days=hoy.weekday())  # weekday(): 0 = lunes
        desde, hasta = lunes - timedelta(weeks=tramos - 1), lunes + timedelta(weeks=1)
    elif agrupar == "mes":
        primero = date(hoy.year, hoy.month, 1)
        desde, hasta = _sumar_meses(primero, -(tramos - 1)), _sumar_meses(primero, 1)
    else:
        desde, hasta = date(hoy.year - (tramos - 1), 1, 1), date(hoy.year + 1, 1, 1)
    return inicio_del_dia(desde), inicio_del_dia(hasta), unidad


def tramo(columna, unidad: str):
    """La expresion SQL que agrupa una columna timestamptz por tramo, en Montevideo.

        date_trunc('week', timezone('America/Montevideo', clase.inicio))

    timezone() pasa el instante a la hora de aca (sin zona) y date_trunc lo
    lleva al principio del tramo: el lunes, el dia 1 o el 1 de enero. De vuelta
    llega un datetime sin zona; etiqueta() lo convierte en texto.

    La unidad y la zona van como texto literal en el SQL, no como parametros.
    Con parametros, el SELECT dice date_trunc($1, ...) y el GROUP BY
    date_trunc($3, ...), y PostgreSQL no los reconoce como la misma expresion.
    No hay riesgo de inyeccion: la unidad sale de AGRUPACIONES y la zona del
    .env, nunca de lo que manda el usuario.
    """
    if unidad not in {u for u, _ in AGRUPACIONES.values()}:
        raise ValueError(f"unidad desconocida: {unidad}")
    return func.date_trunc(
        literal_column(f"'{unidad}'"),
        func.timezone(literal_column(f"'{ajustes.ZONA_HORARIA}'"), columna),
    )


def etiqueta(inicio_tramo: datetime) -> str:
    """El inicio de un tramo -> "AAAA-MM-DD", la etiqueta de los graficos."""
    return inicio_tramo.date().isoformat()


def _sumar_meses(primero: date, meses: int) -> date:
    """El dia 1 de `meses` meses despues (o antes, si es negativo)."""
    indice = primero.year * 12 + primero.month - 1 + meses
    return date(indice // 12, indice % 12 + 1, 1)
