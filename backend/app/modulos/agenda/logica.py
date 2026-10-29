"""Funciones publicas del modulo agenda - dueno P3.

agenda responde una sola pregunta, pero es la mas cara del sistema: cuando
tiene lugar este profesor.

Quien consume que:
  - busqueda -> filtrar_con_hueco(), para el filtro de disponibilidad de 1c
  - busqueda -> primera_hora_libre(), para la columna de resultados y el carrusel
  - clases   -> verificar(), antes de insertar o reprogramar una clase
  - clases   -> hay_bloqueo_encima(), antes de aprobar
  - perfiles -> tiene_franjas(), para no publicar una ficha sin disponibilidad

A quien le pide datos:
  - perfiles -> perfil_profesor_de() y reglas_profesor(), para saber descanso,
                tope y aviso minimo
  - clases   -> clases_aprobadas_entre(), para descontar lo que ya esta ocupado
  - clases   -> clases_entre(), para el calendario semanal de 1i

LOS DOS IDS. Las tablas de agenda cuelgan de perfil_profesor.id, pero todo lo
que llega de afuera (las URLs, clases, busqueda) habla de usuario.id. Las
funciones publicas dicen en el nombre del parametro cual de los dos reciben.

Como en el resto: estas funciones validan y guardan con flush, pero NO hacen
commit. El commit lo hace la ruta.

LA IMPORTACION CIRCULAR. clases importa agenda (para verificar) y agenda
importa clases (para las aprobadas). Funciona porque las dos se importan como
modulo (`import ... as clases`) y solo se usan adentro de las funciones, cuando
las dos ya terminaron de cargarse.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app import fechas
from app.enums import EstadoClase
from app.errores import ErrorAPI, conflicto, no_es_tuyo, no_existe
from app.modulos.agenda.modelos import Bloqueo, FranjaDisponibilidad
from app.modulos.clases import logica as clases
from app.modulos.perfiles import logica as perfiles

# Los huecos arrancan en punto o y media: 14:00, 14:30... nunca 14:10.
PASO = timedelta(minutes=30)

# Las franjas del filtro de 1c, en hora de Montevideo. fin_de_semana es otra
# cosa: sabado y domingo, el dia entero.
FRANJAS_HORARIAS = {
    "manana": (time(6), time(12)),
    "tarde": (time(12), time(18)),
    "noche": (time(18), time(23)),
}
FIN_DE_SEMANA = (0, 6)  # domingo y sabado, con el criterio de dia_semana

# Hasta donde se mira hacia adelante en busqueda.
DIAS_FILTRO = 7
DIAS_PRIMERA_HORA = 14

# Tope del rango de GET /agenda/profesores/{id}/disponibilidad.
MAX_DIAS_RANGO = 31

# Si el profesor no cargo duraciones, se busca lugar para una hora.
DURACION_POR_DEFECTO = 60


# ---------------------------------------------------------------------------
# Lo que se carga de la base para calcular: una "foto" de la agenda de un
# profesor en un rango. Se arma una vez y se consulta en memoria.
# ---------------------------------------------------------------------------

@dataclass
class _Agenda:
    usuario_id: int
    perfil_id: int
    reglas: dict
    # dia_semana -> [(hora_inicio, hora_fin)] de las franjas activas
    franjas: dict[int, list[tuple[time, time]]] = field(default_factory=dict)
    bloqueos: list[tuple[datetime, datetime]] = field(default_factory=list)
    # las aprobadas: [{id, inicio, fin, duracion_min, estudiante_id}]
    clases: list[dict] = field(default_factory=list)

    @property
    def descanso(self) -> timedelta:
        return timedelta(minutes=self.reglas["descanso_min"] or 0)

    @property
    def aviso(self) -> timedelta:
        return timedelta(hours=self.reglas["aviso_minimo_horas"] or 0)

    @property
    def duracion_base(self) -> int:
        """La clase mas corta que ofrece: con esa se pregunta "tiene lugar?"."""
        if self.reglas["duraciones"]:
            return min(self.reglas["duraciones"])
        return self.reglas["duracion_min"] or DURACION_POR_DEFECTO


def _cargar(db: Session, usuario_ids: list[int], desde: datetime, hasta: datetime) -> list[_Agenda]:
    """Las agendas de varios profesores en [desde, hasta), en el orden recibido.

    Franjas y bloqueos van en una consulta cada uno para todos juntos. Las
    clases aprobadas se piden de a un profesor a clases (que es el dueno de la
    tabla); busqueda llama con la lista ya recortada por los otros filtros.
    Los usuarios sin perfil de profesor se saltean.
    """
    agendas = []
    for usuario_id in dict.fromkeys(usuario_ids):  # sin repetidos, en orden
        perfil = perfiles.perfil_profesor_de(db, usuario_id)
        if perfil is not None:
            agendas.append(_Agenda(usuario_id, perfil.id, perfiles.reglas_profesor(db, perfil.id)))
    if not agendas:
        return []

    por_perfil = {a.perfil_id: a for a in agendas}
    franjas = db.scalars(
        select(FranjaDisponibilidad)
        .where(FranjaDisponibilidad.perfil_profesor_id.in_(por_perfil), FranjaDisponibilidad.activa)
        .order_by(FranjaDisponibilidad.hora_inicio)
    )
    for f in franjas:
        por_perfil[f.perfil_profesor_id].franjas.setdefault(f.dia_semana, []).append((f.hora_inicio, f.hora_fin))

    bloqueos = db.scalars(
        select(Bloqueo).where(
            Bloqueo.perfil_profesor_id.in_(por_perfil),
            Bloqueo.inicio < hasta,
            Bloqueo.fin > desde,
        )
    )
    for b in bloqueos:
        por_perfil[b.perfil_profesor_id].bloqueos.append((b.inicio, b.fin))

    for a in agendas:
        a.clases = clases.clases_aprobadas_entre(db, a.usuario_id, desde, hasta)
    return agendas


def _cargar_una(db: Session, profesor_usuario_id: int, desde: datetime, hasta: datetime) -> _Agenda:
    """La agenda de un solo profesor. 404 profesor_no_existe si no es profesor."""
    agendas = _cargar(db, [profesor_usuario_id], desde, hasta)
    if not agendas:
        raise no_existe("profesor")
    return agendas[0]


# ---------------------------------------------------------------------------
# El calculo. Todo trabaja con tramos: pares (inicio, fin) con zona.
# ---------------------------------------------------------------------------

def _dia_semana(dia: date) -> int:
    """0 = domingo ... 6 = sabado, el criterio de la tabla y de Date.getDay().

    isoweekday() de Python es 1 = lunes ... 7 = domingo: el modulo 7 lleva el
    domingo a 0 y deja el resto igual.
    """
    return dia.isoweekday() % 7


def _franjas_del_dia(agenda: _Agenda, dia: date) -> list[tuple[datetime, datetime]]:
    """Las franjas de ese dia, ya con fecha y zona, unidas si se pisan.

    Las franjas son `time` sin zona: se combinan con la fecha EN MONTEVIDEO.
    Si se combinaran en UTC, "martes de 14 a 18" saldria de 11 a 15.
    """
    tramos = sorted(
        (datetime.combine(dia, ini, fechas.ZONA), datetime.combine(dia, fin, fechas.ZONA))
        for ini, fin in agenda.franjas.get(_dia_semana(dia), [])
    )
    unidos: list[tuple[datetime, datetime]] = []
    for ini, fin in tramos:
        if unidos and ini <= unidos[-1][1]:
            unidos[-1] = (unidos[-1][0], max(unidos[-1][1], fin))
        else:
            unidos.append((ini, fin))
    return unidos


def _restar(tramos: list[tuple[datetime, datetime]], ini: datetime, fin: datetime) -> list[tuple[datetime, datetime]]:
    """Los tramos menos [ini, fin). Un tramo puede quedar partido en dos."""
    resultado = []
    for a, b in tramos:
        if fin <= a or ini >= b:
            resultado.append((a, b))
            continue
        if a < ini:
            resultado.append((a, ini))
        if fin < b:
            resultado.append((fin, b))
    return resultado


def _clases_del_dia(agenda: _Agenda, dia: date) -> list[dict]:
    return [c for c in agenda.clases if c["inicio"].astimezone(fechas.ZONA).date() == dia]


def _tramos_libres(agenda: _Agenda, dia: date, ahora: datetime) -> list[tuple[datetime, datetime]]:
    """Los ratos libres de un dia, sin cortar en huecos. Pasos 1 a 6 de huecos_libres()."""
    tope = agenda.reglas["max_clases_dia"]
    if tope and len(_clases_del_dia(agenda, dia)) >= tope:
        return []

    tramos = _franjas_del_dia(agenda, dia)
    for ini, fin in agenda.bloqueos:
        tramos = _restar(tramos, ini, fin)
    # Todas las clases, no solo las de ese dia: el descanso de una clase de las
    # 23:30 puede comerse el principio del dia siguiente.
    for c in agenda.clases:
        tramos = _restar(tramos, c["inicio"] - agenda.descanso, c["fin"] + agenda.descanso)

    limite = ahora + agenda.aviso
    return [(max(a, limite), b) for a, b in tramos if b > limite]


def _redondear(momento: datetime) -> datetime:
    """Lleva un instante al proximo :00 o :30 de Montevideo (si ya esta, no lo mueve)."""
    momento = momento.astimezone(fechas.ZONA)
    base = momento.replace(minute=0, second=0, microsecond=0)
    pasos = -(-(momento - base) // PASO)  # division hacia arriba
    return base + pasos * PASO


def _cortar(tramos: list[tuple[datetime, datetime]], duracion_min: int) -> list[tuple[datetime, datetime]]:
    """Paso 7: los tramos cortados en huecos consecutivos de `duracion_min`.

    Cada hueco arranca en :00 o :30 y no se pisa con el anterior. Con un tramo
    de 14:10 a 18:00 y una hora: 14:30, 15:30 y 16:30 (el de 17:30 no entra).
    """
    duracion = timedelta(minutes=duracion_min)
    huecos = []
    for a, b in tramos:
        inicio = _redondear(a)
        while inicio + duracion <= b:
            huecos.append((inicio, inicio + duracion))
            inicio = _redondear(inicio + duracion)
    return huecos


def _ventana(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """Lo que hay que cargar para calcular de `desde` a `hasta` (inclusive).

    Un dia de mas a cada lado, para que el descanso de las clases de los
    bordes tambien se descuente.
    """
    inicio, fin = fechas.rango_de_dias(desde - timedelta(days=1), hasta + timedelta(days=1))
    return inicio, fin


def _dias(desde: date, hasta: date) -> list[date]:
    return [desde + timedelta(days=n) for n in range((hasta - desde).days + 1)]


# ---------------------------------------------------------------------------
# Las funciones publicas del calculo
# ---------------------------------------------------------------------------

def huecos_libres(db, profesor_usuario_id: int, desde: date, hasta: date, duracion_min: int) -> list[dict]:
    """LA funcion del modulo. Devuelve los ratos libres reales, dia por dia.

    Es lo que dibuja el calendario de 1f y lo que ve el profesor en 1i. El
    frontend solo los pinta: no calcula nada.

    El calculo es una resta sucesiva sobre las franjas de la semana:

      1. Partir de las franjas activas de cada dia del rango.
      2. Restar los bloqueos que pisen ese dia.
      3. Restar las clases APROBADAS (las pendientes no ocupan: varias
         solicitudes sobre el mismo hueco son legitimas).
      4. Restar el descanso_min antes y despues de cada clase ya agendada.
      5. Cortar lo que caiga antes de ahora + aviso_minimo_horas.
      6. Si ese dia ya se llego a max_clases_dia, el dia entero queda sin huecos.
      7. De lo que quedo, quedarse con los tramos donde entre `duracion_min`
         completa, y cortarlos en huecos de esa duracion.

    Vienen TODOS los dias del rango, tambien los que no tienen huecos: asi el
    calendario dibuja la semana entera sin tener que completar nada.

    `hasta` es inclusive. Error: 404 profesor_no_existe.
    """
    agenda = _cargar_una(db, profesor_usuario_id, *_ventana(desde, hasta))
    ahora = fechas.ahora()
    return [
        {
            "fecha": dia.isoformat(),
            "huecos": [
                {"inicio": ini, "fin": fin}
                for ini, fin in _cortar(_tramos_libres(agenda, dia, ahora), duracion_min)
            ],
        }
        for dia in _dias(desde, hasta)
    ]


def verificar(db: Session, profesor_usuario_id: int, inicio: datetime, duracion_min: int) -> dict:
    """Dice si un horario puntual sigue libre, y si no, por que.

    Se llama DOS VECES en el flujo de reserva: al elegir el horario en 1f y de
    nuevo al apretar confirmar en 1g, porque entre una cosa y la otra el hueco
    se pudo ocupar. Y una tercera vez cuando alguien reprograma desde 1b o 1i
    (clases pone la clase en pendiente antes de preguntar, asi su propio
    horario viejo no cuenta como ocupado).

    Devuelve {"libre": True} o {"libre": False, "motivo": "..."} con uno de:
    aviso_minimo, fuera_de_franja, bloqueado, ocupado, tope_diario. Se
    chequean en ese orden y se devuelve el primero que falla.

    Mira el horario pedido tal cual, no los huecos ya cortados: una clase de
    14:15 que entra en la franja es valida aunque el calendario ofrezca 14:00.

    Error: 404 profesor_no_existe.
    """
    inicio = fechas.con_zona(inicio).astimezone(fechas.ZONA)
    fin = inicio + timedelta(minutes=duracion_min)
    dia = inicio.date()
    agenda = _cargar_una(db, profesor_usuario_id, *_ventana(dia, fin.date()))

    if inicio < fechas.ahora() + agenda.aviso:
        return {"libre": False, "motivo": "aviso_minimo"}
    if not any(a <= inicio and fin <= b for a, b in _franjas_del_dia(agenda, dia)):
        return {"libre": False, "motivo": "fuera_de_franja"}
    if any(ini < fin and inicio < fin_b for ini, fin_b in agenda.bloqueos):
        return {"libre": False, "motivo": "bloqueado"}
    if any(c["inicio"] - agenda.descanso < fin and inicio < c["fin"] + agenda.descanso for c in agenda.clases):
        return {"libre": False, "motivo": "ocupado"}
    tope = agenda.reglas["max_clases_dia"]
    if tope and len(_clases_del_dia(agenda, dia)) >= tope:
        return {"libre": False, "motivo": "tope_diario"}
    return {"libre": True}


def filtrar_con_hueco(db: Session, ids_profesor: list[int], dia: int | None, franja: str | None) -> list[int]:
    """De una lista de profesores, cuales tienen hueco real ese dia y esa franja.

    Lo llama busqueda POR DENTRO: no es una ruta HTTP. Es el filtro de
    disponibilidad de 1c.

    `ids_profesor` son usuario.id. `dia` es 0 (domingo) a 6 (sabado); `franja`
    es manana (6 a 12), tarde (12 a 18), noche (18 a 23) o fin_de_semana
    (sabado y domingo enteros). Se mira la semana que viene, desde hoy: "los
    martes de tarde" es "el proximo martes de tarde".

    "Tiene hueco" quiere decir que entra al menos una clase de la duracion mas
    corta que ofrece, con las mismas reglas que el calendario de 1f.

    Recibe la lista YA RECORTADA por los otros filtros y devuelve los que
    pasan, en el mismo orden.
    """
    hoy = fechas.ahora().date()
    dias = [hoy + timedelta(days=n) for n in range(DIAS_FILTRO)]
    if dia is not None:
        dias = [d for d in dias if _dia_semana(d) == dia]
    if franja == "fin_de_semana":
        dias = [d for d in dias if _dia_semana(d) in FIN_DE_SEMANA]
    if not dias or not ids_profesor:
        return []

    def ventana_horaria(d: date) -> tuple[datetime, datetime]:
        if franja in FRANJAS_HORARIAS:
            ini, fin = FRANJAS_HORARIAS[franja]
            return datetime.combine(d, ini, fechas.ZONA), datetime.combine(d, fin, fechas.ZONA)
        return fechas.rango_de_dias(d, d)

    ahora = fechas.ahora()
    con_hueco = []
    for agenda in _cargar(db, ids_profesor, *_ventana(dias[0], dias[-1])):
        for d in dias:
            desde, hasta = ventana_horaria(d)
            # Los mismos huecos que ofrece el calendario de 1f, y de esos los
            # que caen enteros adentro de la franja pedida. No se recortan los
            # tramos antes de cortarlos: con un tramo de 11:30 a 13:00 saldria
            # un hueco a las 12 que el calendario nunca ofrece (ofrece 11:30).
            huecos = _cortar(_tramos_libres(agenda, d, ahora), agenda.duracion_base)
            if any(desde <= ini and fin <= hasta for ini, fin in huecos):
                con_hueco.append(agenda.usuario_id)
                break
    return con_hueco


def primera_hora_libre(db: Session, ids_profesor: list[int]) -> dict[int, datetime]:
    """La proxima hora libre de cada profesor, en lote.

    Es la columna "proxima_hora_libre" de los resultados de 1c y del carrusel
    de 1a. Devuelve {usuario_id: datetime}; el que no tiene nada en las
    proximas dos semanas no viene en el diccionario.

    Mismo calculo que el calendario de 1f, con la duracion mas corta que
    ofrece cada uno.
    """
    if not ids_profesor:
        return {}
    hoy = fechas.ahora().date()
    dias = [hoy + timedelta(days=n) for n in range(DIAS_PRIMERA_HORA)]
    ahora = fechas.ahora()
    resultado = {}
    for agenda in _cargar(db, ids_profesor, *_ventana(dias[0], dias[-1])):
        for d in dias:
            huecos = _cortar(_tramos_libres(agenda, d, ahora), agenda.duracion_base)
            if huecos:
                resultado[agenda.usuario_id] = huecos[0][0]
                break
    return resultado


def hay_bloqueo_encima(db: Session, perfil_profesor_id: int, inicio: datetime, fin: datetime) -> bool:
    """True si un rango pisa algun bloqueo.

    Lo usa la propia agenda al crear un bloqueo nuevo y clases al aprobar.
    OJO: recibe el id del PERFIL.
    """
    return db.scalar(
        select(
            exists().where(
                Bloqueo.perfil_profesor_id == perfil_profesor_id,
                Bloqueo.inicio < fin,
                Bloqueo.fin > inicio,
            )
        )
    )


def tiene_franjas(db: Session, perfil_profesor_id: int) -> bool:
    """True si el profesor cargo al menos una franja activa.

    Lo pide perfiles antes de publicar la ficha: sin franjas el calendario de
    1f sale vacio y nadie puede reservar.
    """
    return db.scalar(
        select(
            exists().where(
                FranjaDisponibilidad.perfil_profesor_id == perfil_profesor_id,
                FranjaDisponibilidad.activa,
            )
        )
    )


# ---------------------------------------------------------------------------
# Lo que edita el profesor desde 1i y 1j
# ---------------------------------------------------------------------------

def perfil_propio(db: Session, usuario_id: int):
    """El perfil de profesor del usuario del token. 404 perfil_no_existe."""
    perfil = perfiles.perfil_profesor_de(db, usuario_id)
    if perfil is None:
        raise no_existe("perfil")
    return perfil


def franjas_de(db: Session, perfil_profesor_id: int) -> list[FranjaDisponibilidad]:
    """Las franjas del profesor, por dia y hora."""
    return list(db.scalars(
        select(FranjaDisponibilidad)
        .where(FranjaDisponibilidad.perfil_profesor_id == perfil_profesor_id)
        .order_by(FranjaDisponibilidad.dia_semana, FranjaDisponibilidad.hora_inicio)
    ))


def reemplazar_franjas(db: Session, perfil_profesor_id: int, nuevas: list) -> list[FranjaDisponibilidad]:
    """Borra todas las franjas del profesor y guarda las que vienen.

    Es un reemplazo completo porque el editor es una grilla: el profesor la
    deja como quiere y guarda una vez. Como la ruta hace un solo commit, o
    queda todo lo nuevo o todo lo viejo.

    Achicar la disponibilidad NO cancela clases ya aprobadas: quedan como
    estan, aunque ahora caigan fuera de las franjas.

    Errores: 400 franja_invalida (hora_fin no es posterior a hora_inicio),
    409 franjas_superpuestas (dos franjas del mismo dia se pisan).
    """
    for f in nuevas:
        if f.hora_fin <= f.hora_inicio:
            raise ErrorAPI(400, "franja_invalida")
    ordenadas = sorted(nuevas, key=lambda f: (f.dia_semana, f.hora_inicio))
    for anterior, siguiente in zip(ordenadas, ordenadas[1:]):
        if anterior.dia_semana == siguiente.dia_semana and siguiente.hora_inicio < anterior.hora_fin:
            raise conflicto("franjas_superpuestas")

    db.execute(delete(FranjaDisponibilidad).where(FranjaDisponibilidad.perfil_profesor_id == perfil_profesor_id))
    db.add_all(
        FranjaDisponibilidad(
            perfil_profesor_id=perfil_profesor_id,
            dia_semana=f.dia_semana,
            hora_inicio=f.hora_inicio,
            hora_fin=f.hora_fin,
            modalidad=f.modalidad,
            activa=f.activa,
        )
        for f in ordenadas
    )
    db.flush()
    return franjas_de(db, perfil_profesor_id)


def bloqueos_entre(db: Session, perfil_profesor_id: int, desde: datetime | None, hasta: datetime | None) -> list[Bloqueo]:
    """Los bloqueos que se cruzan con [desde, hasta), por inicio.

    Sin `desde`, los que todavia no terminaron: es la lista de "proximos
    bloqueos" de 1i, donde los viejos no interesan.
    """
    consulta = select(Bloqueo).where(Bloqueo.perfil_profesor_id == perfil_profesor_id)
    consulta = consulta.where(Bloqueo.fin > (desde if desde is not None else fechas.ahora()))
    if hasta is not None:
        consulta = consulta.where(Bloqueo.inicio < hasta)
    return list(db.scalars(consulta.order_by(Bloqueo.inicio, Bloqueo.id)))


def crear_bloqueo(db: Session, perfil, datos) -> Bloqueo:
    """Bloquea un rato puntual ("el 12 de mayo no puedo").

    Errores:
      400 bloqueo_invalido     fin no es posterior a inicio, o ya paso entero
      409 hay_clase_aprobada   pisa una clase aprobada: primero hay que
                               cancelarla o reprogramarla
      409 bloqueo_superpuesto  pisa otro bloqueo (que lo agrande en vez de
                               duplicarlo)

    Las pendientes que caigan adentro siguen ahi: el profesor las rechaza, y si
    intenta aprobar una, clases responde horario_ocupado.
    """
    inicio, fin = fechas.con_zona(datos.inicio), fechas.con_zona(datos.fin)
    if fin <= inicio or fin <= fechas.ahora():
        raise ErrorAPI(400, "bloqueo_invalido")
    if clases.clases_aprobadas_entre(db, perfil.usuario_id, inicio, fin):
        raise conflicto("hay_clase_aprobada")
    if hay_bloqueo_encima(db, perfil.id, inicio, fin):
        raise conflicto("bloqueo_superpuesto")

    bloqueo = Bloqueo(perfil_profesor_id=perfil.id, inicio=inicio, fin=fin, motivo=_limpio(datos.motivo))
    db.add(bloqueo)
    db.flush()
    return bloqueo


def borrar_bloqueo(db: Session, perfil_profesor_id: int, bloqueo_id: int) -> None:
    """Saca un bloqueo y devuelve ese rato a la disponibilidad.

    Errores: 404 bloqueo_no_existe, 403 no_es_tuyo.
    """
    bloqueo = db.get(Bloqueo, bloqueo_id)
    if bloqueo is None:
        raise no_existe("bloqueo")
    if bloqueo.perfil_profesor_id != perfil_profesor_id:
        raise no_es_tuyo()
    db.delete(bloqueo)
    db.flush()


def semana(db: Session, perfil, desde: date) -> dict:
    """El calendario semanal de 1i: siete dias desde `desde`, inclusive.

    Las clases salen de clases.clases_entre() (con la forma de ClaseOut, la
    misma que GET /clases), separadas por estado. Las canceladas no vienen: en
    el calendario no ocupan nada.
    """
    hasta = desde + timedelta(days=6)
    inicio, fin = fechas.rango_de_dias(desde, hasta)
    filas = clases.clases_entre(db, perfil.usuario_id, inicio, fin)
    por_estado = {
        "aprobadas": (EstadoClase.aprobada,),
        "pendientes": (EstadoClase.pendiente,),
        "cerradas": (EstadoClase.dictada, EstadoClase.no_asistida),
    }
    return {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        **{
            clave: [f for f in filas if f["estado"] in {e.value for e in estados}]
            for clave, estados in por_estado.items()
        },
        "bloqueos": bloqueos_entre(db, perfil.id, inicio, fin),
    }


def _limpio(texto: str | None) -> str | None:
    """Sin espacios de mas, y None si quedo vacio."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None
