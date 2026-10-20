"""Consultas publicas del modulo busqueda - dueno P2.

El modulo no guarda datos propios. Lee las tablas de perfiles y catalogos,
pero no importa sus modelos ORM: describe abajo solamente las columnas que
necesita. Los datos de identidad y materias se completan por la puerta publica
``perfiles.ficha_resumida()``.

Dependencias:
  - perfiles  -> ficha_resumida(), para nombre, foto y materias
  - catalogos -> existe() y centroide_barrio(), para validar y ubicar
  - agenda    -> filtrar_con_hueco() y primera_hora_libre()
"""

from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import Enum, and_, case, column, exists, func, or_, select, table
from sqlalchemy.orm import Session

from app.enums import EstadoFicha, Modalidad
from app.errores import ErrorAPI
from app.modulos.agenda import logica as agenda
from app.modulos.catalogos import logica as catalogos
from app.modulos.perfiles import logica as perfiles


POR_PAGINA = 20
MIN_RESENAS_RANKING = 5
RADIO_TIERRA_KM = 6371.0088


# ---------------------------------------------------------------------------
# Tablas externas vistas "de lejos"
# ---------------------------------------------------------------------------
#
# La regla del proyecto prohibe importar modelos.py de otro modulo. ``table``
# y ``column`` crean descripciones livianas de tablas que ya existen; no crean
# tablas ni duplican modelos. Este es el mismo patron que usa perfiles para
# leer los nombres de catalogos.

_PERFIL_PROFESOR = table(
    "perfil_profesor",
    column("id"),
    column("usuario_id"),
    column("barrio_id"),
    column("latitud"),
    column("longitud"),
    column("modalidad", Enum(Modalidad, name="modalidad_enum")),
    column("precio_hora_presencial"),
    column("precio_hora_online"),
    column("estado_ficha", Enum(EstadoFicha, name="ficha_enum")),
    column("puntaje_promedio"),
    column("cantidad_resenas"),
)

_PROFESOR_MATERIA = table(
    "profesor_materia",
    column("perfil_profesor_id"),
    column("materia_id"),
)

_PROFESOR_ETAPA = table(
    "profesor_etapa",
    column("perfil_profesor_id"),
    column("etapa_id"),
)

_PROFESOR_IDIOMA = table(
    "profesor_idioma",
    column("perfil_profesor_id"),
    column("idioma_id"),
)

_PROFESOR_ZONA = table(
    "profesor_zona",
    column("perfil_profesor_id"),
    column("barrio_id"),
)

_BARRIO = table(
    "barrio",
    column("id"),
    column("nombre"),
    column("latitud"),
    column("longitud"),
)

_CENTRO_EDUCATIVO = table(
    "centro_educativo",
    column("id"),
    column("barrio_id"),
    column("latitud"),
    column("longitud"),
)


# ---------------------------------------------------------------------------
# API interna del modulo
# ---------------------------------------------------------------------------

def buscar(db: Session, filtros) -> dict:
    """Los nueve filtros combinables de 1c, con orden y paginacion.

    El trabajo se divide en cinco pasos faciles de seguir:

      1. SQL descarta fichas no publicadas y aplica materia, etapa, idioma,
         barrio, modalidad, precio y puntaje.
      2. Si se pidio disponibilidad, agenda recibe solamente los ids que ya
         pasaron los filtros baratos.
      3. Se calcula la distancia al barrio o centro elegido y se ordena.
      4. Se corta la pagina de veinte.
      5. perfiles.ficha_resumida() completa nombre, foto y materias en lote.

    ``total`` se calcula antes de paginar, para que el frontend sepa cuantas
    paginas existen.
    """
    _validar_filtros(db, filtros)

    consulta = _aplicar_filtros(_consulta_base(), filtros)
    filas = _leer_filas(db, consulta)

    punto = _punto_referencia(db, filtros.barrio, filtros.centro)
    filas = _agregar_distancias(filas, punto)
    filas = _filtrar_por_disponibilidad(db, filas, filtros.dia, filtros.franja)
    _ordenar(filas, filtros.orden, filtros.modalidad)

    total = len(filas)
    pagina = filtros.pagina
    desde = (pagina - 1) * POR_PAGINA
    pagina_filas = filas[desde:desde + POR_PAGINA]

    ids_pagina = [fila["usuario_id"] for fila in pagina_filas]
    proximas = _primeras_horas_disponibles(db, ids_pagina)

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": POR_PAGINA,
        "resultados": _resultados_busqueda(db, pagina_filas, proximas),
    }


def pines_mapa(db: Session, filtros=None, ids: list[int] | None = None) -> list[dict]:
    """Los pines de Leaflet para 1a, 1c y el mini mapa de 1f.

    Si ``ids`` viene informado, se ignoran los filtros y se conserva el orden
    de esos ids. Sin ids se usa exactamente la misma seleccion que la busqueda,
    pero sin paginar. Un profesor sin coordenadas no puede dibujarse y se
    descarta.
    """
    if ids is not None:
        ids_limpios = list(dict.fromkeys(ids))
        if not ids_limpios:
            return []
        consulta = _consulta_base().where(
            _PERFIL_PROFESOR.c.usuario_id.in_(ids_limpios)
        )
        filas = _leer_filas(db, consulta)
        posicion = {usuario_id: indice for indice, usuario_id in enumerate(ids_limpios)}
        filas.sort(key=lambda fila: posicion.get(fila["usuario_id"], len(posicion)))
    else:
        consulta = _consulta_base()
        if filtros is not None:
            _validar_filtros(db, filtros)
            consulta = _aplicar_filtros(consulta, filtros)
        filas = _leer_filas(db, consulta)
        if filtros is not None:
            filas = _filtrar_por_disponibilidad(
                db, filas, filtros.dia, filtros.franja
            )
            punto = _punto_referencia(db, filtros.barrio, filtros.centro)
            filas = _agregar_distancias(filas, punto)
            _ordenar(filas, filtros.orden, filtros.modalidad)

    dibujables = [
        fila
        for fila in filas
        if fila["latitud"] is not None and fila["longitud"] is not None
    ]
    resumenes = _resumenes_por_id(db, dibujables)
    modalidad_pedida = filtros.modalidad if filtros is not None else None

    pines = []
    for fila in dibujables:
        ficha = resumenes.get(fila["usuario_id"])
        if ficha is None:
            continue
        nombre = f"{ficha['nombre']} {ficha['apellido']}".strip()
        pines.append({
            "id": fila["usuario_id"],
            "nombre": nombre,
            "latitud": fila["latitud"],
            "longitud": fila["longitud"],
            "precio_hora": _precio_fila(fila, modalidad_pedida),
            "puntaje_promedio": fila["puntaje_promedio"],
            "modalidad": fila["modalidad"],
        })
    return pines


def cercanos(
    db: Session,
    barrio_id: int | None = None,
    centro_id: int | None = None,
    con_hueco: bool = False,
    limite: int = 5,
) -> list[dict]:
    """El carrusel "Profes cerca de ti" de 1a.

    Necesita un barrio o un centro como punto de referencia. Solo considera
    fichas publicadas con coordenadas y ordena con la formula de Haversine. Si
    ``con_hueco`` es verdadero, pide a agenda la primera hora libre de cada
    profesor seleccionado.
    """
    if limite <= 0:
        return []
    _validar_ubicacion(db, barrio_id, centro_id)
    punto = _punto_referencia(db, barrio_id, centro_id)
    if punto is None:
        return []

    consulta = _consulta_base().where(
        _PERFIL_PROFESOR.c.latitud.is_not(None),
        _PERFIL_PROFESOR.c.longitud.is_not(None),
    )
    filas = _agregar_distancias(_leer_filas(db, consulta), punto)
    _ordenar(filas, "distancia", None)
    filas = filas[:limite]

    proximas = {}
    if con_hueco:
        proximas = _primeras_horas_disponibles(
            db, [fila["usuario_id"] for fila in filas]
        )
    return _tarjetas_cercanas(db, filas, proximas)


def mejor_puntuados(
    db: Session,
    etapa_id: int | None = None,
    limite: int = 3,
) -> list[dict]:
    """El podio de 1a, opcionalmente limitado a una etapa educativa.

    Exige cinco resenas para que una unica calificacion perfecta no desplace a
    un profesor con trayectoria. Los empates se rompen por cantidad de resenas
    y luego por id, de modo que el orden siempre sea estable.
    """
    if limite <= 0:
        return []
    if etapa_id is not None and not catalogos.existe(db, "etapa_educativa", etapa_id):
        raise ErrorAPI(400, "etapa_no_existe")

    consulta = _consulta_base().where(
        _PERFIL_PROFESOR.c.cantidad_resenas >= MIN_RESENAS_RANKING
    )
    if etapa_id is not None:
        consulta = consulta.where(
            _existe_relacion(
                _PROFESOR_ETAPA,
                _PROFESOR_ETAPA.c.etapa_id == etapa_id,
            )
        )
    consulta = consulta.order_by(
        _PERFIL_PROFESOR.c.puntaje_promedio.desc(),
        _PERFIL_PROFESOR.c.cantidad_resenas.desc(),
        _PERFIL_PROFESOR.c.usuario_id,
    ).limit(limite)

    return _tarjetas_cercanas(db, _leer_filas(db, consulta), {})


# ---------------------------------------------------------------------------
# Construccion de la consulta
# ---------------------------------------------------------------------------

def _consulta_base():
    """Columnas comunes a resultados, pines, cercanos y ranking."""
    return (
        select(
            _PERFIL_PROFESOR.c.id.label("perfil_id"),
            _PERFIL_PROFESOR.c.usuario_id,
            _PERFIL_PROFESOR.c.barrio_id,
            _BARRIO.c.nombre.label("barrio"),
            _PERFIL_PROFESOR.c.latitud,
            _PERFIL_PROFESOR.c.longitud,
            _PERFIL_PROFESOR.c.modalidad,
            _PERFIL_PROFESOR.c.precio_hora_presencial,
            _PERFIL_PROFESOR.c.precio_hora_online,
            _PERFIL_PROFESOR.c.puntaje_promedio,
            _PERFIL_PROFESOR.c.cantidad_resenas,
        )
        .select_from(
            _PERFIL_PROFESOR.outerjoin(
                _BARRIO,
                _BARRIO.c.id == _PERFIL_PROFESOR.c.barrio_id,
            )
        )
        .where(
            _PERFIL_PROFESOR.c.estado_ficha == EstadoFicha.publicada
        )
    )


def _aplicar_filtros(consulta, filtros):
    """Agrega solamente las condiciones correspondientes a filtros presentes."""
    if filtros.materia is not None:
        consulta = consulta.where(
            _existe_relacion(
                _PROFESOR_MATERIA,
                _PROFESOR_MATERIA.c.materia_id == filtros.materia,
            )
        )
    if filtros.etapa is not None:
        consulta = consulta.where(
            _existe_relacion(
                _PROFESOR_ETAPA,
                _PROFESOR_ETAPA.c.etapa_id == filtros.etapa,
            )
        )
    if filtros.idioma is not None:
        consulta = consulta.where(
            _existe_relacion(
                _PROFESOR_IDIOMA,
                _PROFESOR_IDIOMA.c.idioma_id == filtros.idioma,
            )
        )
    if filtros.barrio is not None:
        consulta = consulta.where(
            or_(
                _PERFIL_PROFESOR.c.barrio_id == filtros.barrio,
                _existe_relacion(
                    _PROFESOR_ZONA,
                    _PROFESOR_ZONA.c.barrio_id == filtros.barrio,
                ),
            )
        )

    if filtros.modalidad == Modalidad.presencial.value:
        consulta = consulta.where(
            _PERFIL_PROFESOR.c.modalidad.in_([
                Modalidad.presencial,
                Modalidad.ambas,
            ])
        )
    elif filtros.modalidad == Modalidad.online.value:
        consulta = consulta.where(
            _PERFIL_PROFESOR.c.modalidad.in_([
                Modalidad.online,
                Modalidad.ambas,
            ])
        )
    elif filtros.modalidad == Modalidad.ambas.value:
        consulta = consulta.where(
            _PERFIL_PROFESOR.c.modalidad == Modalidad.ambas
        )

    precio = _precio_sql(filtros.modalidad)
    if filtros.precio_min is not None:
        consulta = consulta.where(precio >= filtros.precio_min)
    if filtros.precio_max is not None:
        consulta = consulta.where(precio <= filtros.precio_max)
    if filtros.puntaje_min is not None:
        consulta = consulta.where(
            _PERFIL_PROFESOR.c.puntaje_promedio >= filtros.puntaje_min
        )
    return consulta


def _existe_relacion(tabla_relacion, condicion):
    """EXISTS correlacionado con el perfil actual, sin duplicar filas."""
    return exists(
        select(1)
        .select_from(tabla_relacion)
        .where(
            and_(
                tabla_relacion.c.perfil_profesor_id == _PERFIL_PROFESOR.c.id,
                condicion,
            )
        )
    )


def _precio_sql(modalidad: str | None):
    """La columna de precio que corresponde al filtro solicitado."""
    if modalidad == Modalidad.presencial.value:
        return _PERFIL_PROFESOR.c.precio_hora_presencial
    if modalidad == Modalidad.online.value:
        return _PERFIL_PROFESOR.c.precio_hora_online

    # Sin modalidad, el precio representativo es el mas barato que ofrece.
    # Los dos primeros casos evitan que un NULL anule el otro precio.
    return case(
        (
            _PERFIL_PROFESOR.c.precio_hora_presencial.is_(None),
            _PERFIL_PROFESOR.c.precio_hora_online,
        ),
        (
            _PERFIL_PROFESOR.c.precio_hora_online.is_(None),
            _PERFIL_PROFESOR.c.precio_hora_presencial,
        ),
        else_=func.least(
            _PERFIL_PROFESOR.c.precio_hora_presencial,
            _PERFIL_PROFESOR.c.precio_hora_online,
        ),
    )


# ---------------------------------------------------------------------------
# Validacion y ubicacion
# ---------------------------------------------------------------------------

def _validar_filtros(db: Session, filtros) -> None:
    catalogos_pedidos = (
        ("materia", "materia", filtros.materia),
        ("etapa_educativa", "etapa", filtros.etapa),
        ("centro_educativo", "centro", filtros.centro),
        ("barrio", "barrio", filtros.barrio),
        ("idioma", "idioma", filtros.idioma),
    )
    for tabla, nombre, id_ in catalogos_pedidos:
        if id_ is not None and not catalogos.existe(db, tabla, id_):
            raise ErrorAPI(400, f"{nombre}_no_existe")

    if (
        filtros.precio_min is not None
        and filtros.precio_max is not None
        and filtros.precio_min > filtros.precio_max
    ):
        raise ErrorAPI(400, "rango_precio_invalido")


def _validar_ubicacion(
    db: Session,
    barrio_id: int | None,
    centro_id: int | None,
) -> None:
    if barrio_id is not None and not catalogos.existe(db, "barrio", barrio_id):
        raise ErrorAPI(400, "barrio_no_existe")
    if centro_id is not None and not catalogos.existe(
        db, "centro_educativo", centro_id
    ):
        raise ErrorAPI(400, "centro_no_existe")


def _punto_referencia(
    db: Session,
    barrio_id: int | None,
    centro_id: int | None,
) -> tuple[Decimal, Decimal] | None:
    """El centro tiene prioridad; si no hay, usa el centroide del barrio."""
    if centro_id is not None:
        fila = db.execute(
            select(
                _CENTRO_EDUCATIVO.c.latitud,
                _CENTRO_EDUCATIVO.c.longitud,
            ).where(_CENTRO_EDUCATIVO.c.id == centro_id)
        ).one_or_none()
        if fila is None or fila.latitud is None or fila.longitud is None:
            return None
        return fila.latitud, fila.longitud
    if barrio_id is not None:
        return catalogos.centroide_barrio(db, barrio_id)
    return None


# ---------------------------------------------------------------------------
# Transformacion de resultados
# ---------------------------------------------------------------------------

def _leer_filas(db: Session, consulta) -> list[dict]:
    filas = db.execute(consulta).mappings().all()
    resultado = []
    for fila in filas:
        item = dict(fila)
        item["modalidad"] = _valor_enum(item["modalidad"])
        resultado.append(item)
    return resultado


def _agregar_distancias(
    filas: list[dict],
    punto: tuple[Decimal, Decimal] | None,
) -> list[dict]:
    resultado = []
    for fila in filas:
        item = dict(fila)
        if punto is None or item["latitud"] is None or item["longitud"] is None:
            item["distancia_km"] = None
        else:
            item["distancia_km"] = _distancia_km(
                punto[0],
                punto[1],
                item["latitud"],
                item["longitud"],
            )
        resultado.append(item)
    return resultado


def _filtrar_por_disponibilidad(
    db: Session,
    filas: list[dict],
    dia: int | None,
    franja: str | None,
) -> list[dict]:
    if dia is None and franja is None:
        return filas
    ids = [fila["usuario_id"] for fila in filas]
    permitidos = set(agenda.filtrar_con_hueco(db, ids, dia, franja))
    return [fila for fila in filas if fila["usuario_id"] in permitidos]


def _ordenar(filas: list[dict], orden: str, modalidad: str | None) -> None:
    if orden == "puntaje":
        filas.sort(key=lambda fila: (
            -float(fila["puntaje_promedio"] or 0),
            -int(fila["cantidad_resenas"] or 0),
            fila["usuario_id"],
        ))
        return
    if orden == "precio":
        filas.sort(key=lambda fila: (
            _precio_fila(fila, modalidad) is None,
            float(_precio_fila(fila, modalidad) or 0),
            -float(fila["puntaje_promedio"] or 0),
            fila["usuario_id"],
        ))
        return

    # Distancias desconocidas van al final. Puntaje rompe los empates y
    # tambien da un orden util cuando no se eligio barrio ni centro.
    filas.sort(key=lambda fila: (
        fila.get("distancia_km") is None,
        float(fila.get("distancia_km") or 0),
        -float(fila["puntaje_promedio"] or 0),
        fila["usuario_id"],
    ))


def _resultados_busqueda(
    db: Session,
    filas: list[dict],
    proximas: dict,
) -> list[dict]:
    resumenes = _resumenes_por_id(db, filas)
    resultados = []
    for fila in filas:
        resumen = resumenes.get(fila["usuario_id"])
        if resumen is None:
            continue
        item = dict(resumen)
        # ficha_resumida trae un precio minimo para tarjetas compactas; 1c
        # muestra ambos precios, asi que ese campo no forma parte de esta salida.
        item.pop("precio_hora", None)
        item.update({
            "barrio": fila["barrio"],
            "modalidad": fila["modalidad"],
            "precio_hora_presencial": fila["precio_hora_presencial"],
            "precio_hora_online": fila["precio_hora_online"],
            "puntaje_promedio": fila["puntaje_promedio"],
            "cantidad_resenas": fila["cantidad_resenas"],
            "distancia_km": fila.get("distancia_km"),
            "proxima_hora_libre": proximas.get(fila["usuario_id"]),
        })
        resultados.append(item)
    return resultados


def _tarjetas_cercanas(
    db: Session,
    filas: list[dict],
    proximas: dict,
) -> list[dict]:
    resumenes = _resumenes_por_id(db, filas)
    tarjetas = []
    for fila in filas:
        resumen = resumenes.get(fila["usuario_id"])
        if resumen is None:
            continue
        item = dict(resumen)
        item.update({
            "barrio": fila["barrio"],
            "distancia_km": fila.get("distancia_km"),
            "modalidad": fila["modalidad"],
            "precio_hora": _precio_fila(fila, None),
            "puntaje_promedio": fila["puntaje_promedio"],
            "cantidad_resenas": fila["cantidad_resenas"],
            "primera_hora_libre": proximas.get(fila["usuario_id"]),
        })
        tarjetas.append(item)
    return tarjetas


def _resumenes_por_id(db: Session, filas: list[dict]) -> dict[int, dict]:
    ids = [fila["usuario_id"] for fila in filas]
    return {ficha["id"]: ficha for ficha in perfiles.ficha_resumida(db, ids)}


def _primeras_horas_disponibles(db: Session, ids: list[int]) -> dict:
    """Integra P3 sin bloquear las busquedas basicas mientras P3 esta pendiente.

    Cuando agenda implemente primera_hora_libre(), su resultado se usa sin
    cambios. Hasta entonces las respuestas llevan el campo opcional en null.
    Los filtros explicitos por dia/franja no se ocultan: esos si requieren que
    P3 este terminado y dejan propagar su NotImplementedError actual.
    """
    if not ids:
        return {}
    try:
        return agenda.primera_hora_libre(db, ids)
    except NotImplementedError:
        return {}


def _precio_fila(fila: dict, modalidad: str | None) -> Decimal | None:
    if modalidad == Modalidad.presencial.value:
        return fila["precio_hora_presencial"]
    if modalidad == Modalidad.online.value:
        return fila["precio_hora_online"]
    precios = [
        precio
        for precio in (
            fila["precio_hora_presencial"],
            fila["precio_hora_online"],
        )
        if precio is not None
    ]
    return min(precios) if precios else None


def _distancia_km(lat1, lon1, lat2, lon2) -> float:
    """Distancia de Haversine entre dos coordenadas, redondeada a 10 metros."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(
        radians,
        (float(lat1), float(lon1), float(lat2), float(lon2)),
    )
    diferencia_lat = lat2_r - lat1_r
    diferencia_lon = lon2_r - lon1_r
    a = (
        sin(diferencia_lat / 2) ** 2
        + cos(lat1_r) * cos(lat2_r) * sin(diferencia_lon / 2) ** 2
    )
    return round(2 * RADIO_TIERRA_KM * asin(sqrt(a)), 2)


def _valor_enum(valor):
    return getattr(valor, "value", valor)
