"""Funciones publicas del modulo pagos - dueno P4.

El cobro es SIMULADO de punta a punta. No hay pasarela: los datos de la tarjeta
se guardan en la base y el cobro es un registro que cambia de estado. Siempre
responde bien, salvo que se fuerce el error a proposito para probar 1g.

Quien consume que:
  - clases -> retener() al crear, cobrar() al aprobar, liberar() al rechazar,
              reembolsar() al cancelar
  - clases -> cobro_de() y estados_de_cobro(), para saber en que anda la plata
              de una clase sin leer esta tabla

Las cuatro primeras son las cuatro transiciones del estado de un cobro, y son
la unica forma de escribir en esa tabla.

Como en cuentas y perfiles: estas funciones validan y guardan, pero NO hacen
commit (lo hace la ruta, o clases, que orquesta la transaccion entera). La
unica excepcion es reembolsar(), que corre despues de la request con su
propia sesion (ver su docstring).
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Enum, column, func, select, table
from sqlalchemy.orm import Session

from app import fechas
from app.db import SesionLocal
from app.enums import EstadoClase, EstadoCobro
from app.errores import ErrorAPI, conflicto, no_es_tuyo, no_existe
from app.modulos.cuentas import logica as cuentas
from app.modulos.pagos.modelos import Cobro, Tarjeta

# Filas por pagina del historial de 1e.
POR_PAGINA = 50

# ---------------------------------------------------------------------------
# La clase y la materia, vistas "de lejos"
# ---------------------------------------------------------------------------
#
# El historial necesita la materia y el profesor de cada cobro, y los ingresos
# filtran por profesor. Esos datos estan en la tabla clase, que es del modulo
# clases. No se puede importar clases/modelos.py (la regla dura), ni
# clases/logica.py (clases ya importa este archivo: seria una importacion
# circular). Asi que se describen a mano, por NOMBRE de tabla y solo con las
# columnas que hacen falta, igual que perfiles hace con los catalogos. Solo
# para LEER: nada de pagos escribe en clase.
#
# estado lleva su tipo: sin el, SQLAlchemy manda 'dictada' como texto y
# PostgreSQL no sabe comparar clase_enum con varchar.
_CLASE = table(
    "clase",
    column("id"), column("estudiante_id"), column("profesor_id"),
    column("materia_id"), column("estado", Enum(EstadoClase, name="clase_enum")), column("inicio"),
)
_MATERIA = table("materia", column("id"), column("nombre"))


# ---------------------------------------------------------------------------
# Las cuatro transiciones del cobro. Las llama clases.
# ---------------------------------------------------------------------------

def retener(db: Session, clase_id: int, tarjeta_id: int, importe: Decimal, estudiante_id: int) -> Cobro:
    """Crea el cobro en estado retenido. Lo llama clases al crear la clase.

    Retenido quiere decir: el alumno ya puso la tarjeta, pero el profesor
    todavia no acepto. Si rechaza, se libera y no se cobro nada.

    `estudiante_id` es el duenio de la clase: la tarjeta tiene que ser suya.
    Sin commit: lo hace clases, que esta orquestando la transaccion entera. Si
    esto falla, la clase que clases ya inserto se descarta con el rollback.
    """
    # 1. La tarjeta tiene que existir, estar activa y ser del alumno. Si es de
    #    otro, tambien 404: no hace falta confirmarle que esa tarjeta existe.
    tarjeta = db.get(Tarjeta, tarjeta_id)
    if tarjeta is None or not tarjeta.activa or tarjeta.usuario_id != estudiante_id:
        raise no_existe("tarjeta")

    # 2. Vencida -> 402, igual que lo diria una pasarela.
    if _vencida(tarjeta.vence_mes, tarjeta.vence_anio):
        raise ErrorAPI(402, "tarjeta_vencida")

    # 3. EL GANCHO PARA PROBAR EL ERROR DE 1g. El cobro es simulado y siempre
    #    sale bien, salvo con una tarjeta terminada en 0000: asi se puede ver
    #    el cartel de "la tarjeta rechazo el pago" sin tocar codigo.
    if tarjeta.numero.endswith("0000"):
        raise ErrorAPI(402, "cobro_rechazado")

    # 4. El cobro, con el importe copiado: si la clase cambiara, el movimiento
    #    de plata ya registrado no cambia con ella.
    cobro = Cobro(
        clase_id=clase_id,
        tarjeta_id=tarjeta.id,
        importe=importe,
        estado=EstadoCobro.retenido,
        retenido_el=fechas.ahora(),
    )
    db.add(cobro)
    db.flush()
    return cobro


def cobrar(db: Session, clase_id: int) -> Cobro:
    """Pasa el cobro de retenido a cobrado. Lo llama clases al aprobar.

    A partir de aca el importe cuenta en los ingresos del profesor.

    Si YA esta cobrado no hace nada: pasa cuando se aprueba de nuevo una clase
    que estaba aprobada y se reprogramo (reprogramar la vuelve a pendiente,
    pero la plata ya se habia cobrado y no se cobra dos veces).
    409 estado_invalido si esta liberado o reembolsado.
    """
    cobro = _cobro(db, clase_id)
    if cobro.estado == EstadoCobro.cobrado:
        return cobro
    if cobro.estado != EstadoCobro.retenido:
        raise conflicto("estado_invalido")
    cobro.estado = EstadoCobro.cobrado
    cobro.cobrado_el = fechas.ahora()
    db.flush()
    return cobro


def liberar(db: Session, clase_id: int) -> Cobro:
    """Pasa el cobro de retenido a liberado. Lo llama clases al RECHAZAR, y al
    cancelar una clase que todavia estaba pendiente.

    Importante: se llama ANTES de borrar la clase. La clase rechazada
    desaparece, pero el cobro liberado queda como registro de que hubo un
    movimiento (con clase_id en NULL, por el ON DELETE SET NULL).

    Un caso borde: una clase aprobada que se reprogramo vuelve a pendiente con
    el cobro YA cobrado. Si el profesor la rechaza, no hay retencion que
    soltar: la plata se cobro y hay que devolverla. Se marca reembolsado en el
    momento, y no en segundo plano como al cancelar, porque la clase se borra
    enseguida y la tarea no tendria por donde encontrar el cobro.
    """
    cobro = _cobro(db, clase_id)
    if cobro.estado == EstadoCobro.retenido:
        cobro.estado = EstadoCobro.liberado
        cobro.liberado_el = fechas.ahora()
    elif cobro.estado == EstadoCobro.cobrado:
        cobro.estado = EstadoCobro.reembolsado
        cobro.reembolsado_el = fechas.ahora()
    else:
        raise conflicto("estado_invalido")
    db.flush()
    return cobro


def reembolsar(clase_id: int) -> None:
    """Devuelve el importe al alumno. Corre como BackgroundTask al cancelar.

    OJO: esta funcion NO recibe la sesion de la request. Corre despues de que
    la respuesta ya se envio, y para entonces esa sesion esta cerrada. Por eso
    abre la suya con SesionLocal(), hace su propio commit y la cierra al
    terminar. Es la unica funcion de pagos que hace commit.

    Es IDEMPOTENTE: si se encola dos veces, no puede devolver la plata dos
    veces. El FOR UPDATE bloquea la fila mientras tanto: si dos corren a la
    vez, la segunda espera, ve el cobro ya reembolsado y no hace nada.

    No hace falta "descontarle" nada al profesor: sus ingresos son la suma de
    los cobros en estado cobrado, y este deja de estarlo.

    PENDIENTE DE DECIDIR (seccion 12.2 de la documentacion): la politica de
    cancelacion. Si se reembolsa el total siempre, o si hay un plazo minimo
    (por ejemplo, cancelar con menos de 24 horas). Hoy se devuelve el TOTAL
    siempre: el estado cambia y el importe queda como estaba.
    """
    db = SesionLocal()
    try:
        cobro = db.scalar(select(Cobro).where(Cobro.clase_id == clase_id).with_for_update())
        # Solo se reembolsa lo cobrado. Si ya esta reembolsado (se encolo dos
        # veces) o no existe, no hay nada que hacer.
        if cobro is None or cobro.estado != EstadoCobro.cobrado:
            return
        cobro.estado = EstadoCobro.reembolsado
        cobro.reembolsado_el = fechas.ahora()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        # Siempre, incluso si algo fallo: si no, la conexion queda tomada.
        db.close()


# ---------------------------------------------------------------------------
# Lectura del cobro de una clase. La usa clases.
# ---------------------------------------------------------------------------

def cobro_de(db: Session, clase_id: int) -> dict | None:
    """{"estado": "retenido", "importe": Decimal} del cobro de una clase, o None.

    clases lo usa al cancelar, para decidir si libera en el momento (retenido)
    o encola el reembolso (cobrado), y para informar cuanto se devuelve.
    """
    cobro = db.scalar(select(Cobro).where(Cobro.clase_id == clase_id))
    if cobro is None:
        return None
    return {"estado": cobro.estado.value, "importe": cobro.importe}


def estados_de_cobro(db: Session, clase_ids: list[int]) -> dict[int, str]:
    """{clase_id: estado del cobro} para varias clases, en UNA consulta.

    Es el cobro_estado de cada fila del calendario (GET /clases): con una
    consulta por clase serian 50 por pagina.
    """
    if not clase_ids:
        return {}
    filas = db.execute(select(Cobro.clase_id, Cobro.estado).where(Cobro.clase_id.in_(clase_ids)))
    return {fila.clase_id: fila.estado.value for fila in filas}


# ---------------------------------------------------------------------------
# Tarjetas - 1e y 1g
# ---------------------------------------------------------------------------

def tarjetas_de(db: Session, usuario_id: int) -> list[dict]:
    """Las tarjetas ACTIVAS del alumno, en su version segura (ver _segura)."""
    tarjetas = db.scalars(
        select(Tarjeta)
        .where(Tarjeta.usuario_id == usuario_id, Tarjeta.activa.is_(True))
        .order_by(Tarjeta.id)
    )
    return [_segura(t) for t in tarjetas]


def agregar_tarjeta(db: Session, usuario_id: int, datos) -> dict:
    """Guarda una tarjeta nueva y la devuelve en su version segura.

    `datos` es un TarjetaIn. Se guarda tal cual, sin pasarela: ver la
    advertencia de pagos/modelos.py.

    Errores: 400 tarjeta_invalida (el numero o el CCV no son solo digitos, o el
             anio no tiene cuatro cifras), 402 tarjeta_vencida.
    """
    # 1. El frontend puede mandar el numero como se lee en la tarjeta,
    #    "4111 1111 1111 1111": los espacios se sacan antes de validar.
    #    isascii() porque isdigit() solo tambien acepta cosas como "²".
    numero = datos.numero.replace(" ", "")
    ccv = datos.ccv.strip()
    titular = datos.titular.strip()
    numero_valido = numero.isascii() and numero.isdigit() and 13 <= len(numero) <= 19
    ccv_valido = ccv.isascii() and ccv.isdigit()
    # El anio va con cuatro cifras (2028). Con "28" la tarjeta pareceria
    # vencida hace dos mil anios, y el error diria otra cosa.
    anio_valido = 2000 <= datos.vence_anio <= 2099
    if not (numero_valido and ccv_valido and anio_valido and titular):
        raise ErrorAPI(400, "tarjeta_invalida")

    # 2. Una tarjeta vencida no sirve para nada: no se guarda.
    if _vencida(datos.vence_mes, datos.vence_anio):
        raise ErrorAPI(402, "tarjeta_vencida")

    tarjeta = Tarjeta(
        usuario_id=usuario_id,
        numero=numero,
        titular=titular.upper(),  # como esta impreso en la tarjeta
        vence_mes=datos.vence_mes,
        vence_anio=datos.vence_anio,
        ccv=ccv,
    )
    db.add(tarjeta)
    db.flush()  # para tener tarjeta.id
    return _segura(tarjeta)


def dar_de_baja_tarjeta(db: Session, usuario_id: int, tarjeta_id: int) -> None:
    """Baja LOGICA (activa = false), no DELETE.

    Los cobros viejos apuntan a esta fila, y el historial de 1e tiene que poder
    seguir diciendo con que se pago.

    Errores: 404 tarjeta_no_existe (o ya estaba dada de baja),
             403 no_es_tuyo (es de otro alumno).
    """
    tarjeta = db.get(Tarjeta, tarjeta_id)
    if tarjeta is None:
        raise no_existe("tarjeta")
    if tarjeta.usuario_id != usuario_id:
        raise no_es_tuyo()
    if not tarjeta.activa:
        raise no_existe("tarjeta")
    tarjeta.activa = False
    db.flush()


def marca_de(numero: str) -> str:
    """Deduce la marca a partir del numero. Util, no critico.

    4 -> Visa, 5 -> Mastercard, el resto -> Otra.
    """
    if numero.startswith("4"):
        return "Visa"
    if numero.startswith("5"):
        return "Mastercard"
    return "Otra"


# ---------------------------------------------------------------------------
# Historial del alumno - 1e
# ---------------------------------------------------------------------------

def historial_de(db: Session, usuario_id: int, desde: datetime | None, hasta: datetime | None,
                 pagina: int = 1) -> list[dict]:
    """Los movimientos de plata del alumno, del mas nuevo al mas viejo.

    Son sus filas de cobro, con materia y profesor de la clase. Incluye los
    reembolsos de las canceladas y los liberados de las rechazadas.

    POR QUE SE FILTRA POR LA TARJETA Y NO POR LA CLASE: la clase rechazada se
    borro, y su cobro quedo con clase_id en NULL. Filtrando por
    clase.estudiante_id esos cobros desaparecerian del historial. La tarjeta,
    en cambio, es del alumno y no se borra nunca (la baja es logica), y
    retener() siempre la guarda. Por eso se va por tarjeta.usuario_id, y la
    clase entra con LEFT JOIN: si no esta, materia y contraparte quedan en null.

    `desde` y `hasta` son instantes ya armados (ver fechas.rango_de_dias), y se
    comparan contra la fecha del ultimo movimiento.
    """
    # La fecha del movimiento: la del ultimo cambio de estado que tuvo.
    fecha = func.coalesce(
        Cobro.reembolsado_el, Cobro.liberado_el, Cobro.cobrado_el, Cobro.retenido_el
    )
    consulta = (
        select(
            Cobro.id, fecha.label("fecha"), Cobro.clase_id, Cobro.importe, Cobro.estado,
            _CLASE.c.profesor_id, _MATERIA.c.nombre.label("materia"),
        )
        .select_from(Cobro)
        .join(Tarjeta, Tarjeta.id == Cobro.tarjeta_id)
        .outerjoin(_CLASE, _CLASE.c.id == Cobro.clase_id)
        .outerjoin(_MATERIA, _MATERIA.c.id == _CLASE.c.materia_id)
        .where(Tarjeta.usuario_id == usuario_id)
    )
    if desde is not None:
        consulta = consulta.where(fecha >= desde)
    if hasta is not None:
        consulta = consulta.where(fecha < hasta)
    filas = db.execute(
        consulta.order_by(fecha.desc(), Cobro.id.desc())
        .limit(POR_PAGINA)
        .offset((pagina - 1) * POR_PAGINA)
    ).all()

    # El nombre de los profesores, todos juntos (no uno por fila).
    profesores = cuentas.datos_basicos_varios(db, list({f.profesor_id for f in filas if f.profesor_id}))
    return [
        {
            "id": f.id,
            "fecha": f.fecha,
            "clase_id": f.clase_id,
            "materia": f.materia,
            "contraparte": _nombre_completo(profesores.get(f.profesor_id)),
            "importe": f.importe,
            "estado": f.estado.value,
        }
        for f in filas
    ]


# ---------------------------------------------------------------------------
# Ingresos del profesor - 1d y 1j
# ---------------------------------------------------------------------------

def ingresos_de(db: Session, profesor_usuario_id: int, periodo: str, agrupar: str = "semana") -> dict:
    """Los ingresos del profesor. Compartido por el panel 1d y el perfil 1j.

    Todo sale de cobro, no hay tabla de liquidaciones:
      cobrado    sum(importe) de sus cobros en estado cobrado, cobrados en el
                 periodo (por cobrado_el)
      pendiente  sum(importe) de los retenidos en el periodo (por retenido_el),
                 o sea lo que espera que el profesor apruebe
      promedio   cobrado dividido la cantidad de clases dictadas del periodo
                 (0 si no dicto ninguna)
      serie      lo cobrado por tramo (semana, mes o anio), con la misma
                 ventana que GET /clases/series, para el grafico de 1d

    `periodo` es mes, trimestre o anio: el calendario en curso (ver
    fechas.rango_periodo). Errores: 400 periodo_invalido, 400 agrupacion_invalida.

    El "de quien" va por clase.profesor_id: el cobro no sabe de quien es.
    """
    desde, hasta = fechas.rango_periodo(periodo)
    cobrado = _suma(db, profesor_usuario_id, EstadoCobro.cobrado, Cobro.cobrado_el, desde, hasta)
    pendiente = _suma(db, profesor_usuario_id, EstadoCobro.retenido, Cobro.retenido_el, desde, hasta)

    dictadas = db.scalar(
        select(func.count()).select_from(_CLASE).where(
            _CLASE.c.profesor_id == profesor_usuario_id,
            _CLASE.c.estado == EstadoClase.dictada,
            _CLASE.c.inicio >= desde,
            _CLASE.c.inicio < hasta,
        )
    )
    promedio = _centesimos(cobrado / dictadas) if dictadas else Decimal("0.00")

    # La serie: date_trunc en la zona de Montevideo, ver fechas.tramo().
    v_desde, v_hasta, unidad = fechas.ventana(agrupar)
    tramo = fechas.tramo(Cobro.cobrado_el, unidad)
    filas = db.execute(
        select(tramo.label("tramo"), func.sum(Cobro.importe).label("importe"))
        .select_from(Cobro)
        .join(_CLASE, _CLASE.c.id == Cobro.clase_id)
        .where(
            _CLASE.c.profesor_id == profesor_usuario_id,
            Cobro.estado == EstadoCobro.cobrado,
            Cobro.cobrado_el >= v_desde,
            Cobro.cobrado_el < v_hasta,
        )
        .group_by(tramo)
        .order_by(tramo)
    )
    return {
        "cobrado": cobrado,
        "pendiente": pendiente,
        "promedio_por_clase": promedio,
        # Los tramos sin cobros no aparecen: el frontend los completa con 0.
        "serie": [{"etiqueta": fechas.etiqueta(f.tramo), "importe": f.importe} for f in filas],
    }


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------

def _cobro(db: Session, clase_id: int) -> Cobro:
    """El cobro de una clase, para modificarlo. 404 si no tiene.

    No deberia pasar nunca (crear la clase y retener van en la misma
    transaccion), pero si alguien toco la base a mano, mejor un error claro.
    """
    cobro = db.scalar(select(Cobro).where(Cobro.clase_id == clase_id))
    if cobro is None:
        raise no_existe("cobro")
    return cobro


def _suma(db: Session, profesor_id: int, estado: EstadoCobro, columna_fecha, desde, hasta) -> Decimal:
    """sum(importe) de los cobros del profesor en `estado`, con la fecha en el rango."""
    return db.scalar(
        select(func.coalesce(func.sum(Cobro.importe), 0))
        .select_from(Cobro)
        .join(_CLASE, _CLASE.c.id == Cobro.clase_id)
        .where(
            _CLASE.c.profesor_id == profesor_id,
            Cobro.estado == estado,
            columna_fecha >= desde,
            columna_fecha < hasta,
        )
    )


def _segura(tarjeta: Tarjeta) -> dict:
    """La forma de TarjetaOut: NUNCA el numero completo ni el CCV.

    Con la marca, los ultimos cuatro y el vencimiento alcanza para que el
    alumno reconozca cual es.
    """
    return {
        "id": tarjeta.id,
        "marca": marca_de(tarjeta.numero),
        "ultimos4": tarjeta.numero[-4:],
        "titular": tarjeta.titular,
        "vence": f"{tarjeta.vence_mes:02d}/{tarjeta.vence_anio % 100:02d}",  # "MM/AA"
    }


def _vencida(mes: int, anio: int) -> bool:
    """True si la tarjeta ya vencio. Vale hasta el ultimo dia de su mes."""
    hoy = fechas.ahora().date()
    return (anio, mes) < (hoy.year, hoy.month)


def _centesimos(valor: Decimal) -> Decimal:
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _nombre_completo(persona: dict | None) -> str | None:
    if persona is None:
        return None
    return f"{persona['nombre']} {persona['apellido']}"
