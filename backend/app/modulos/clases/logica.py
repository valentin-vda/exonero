"""Funciones publicas del modulo clases - dueno P4.

clases es el modulo mas pesado y el de mayor riesgo: maneja estados y plata.

Quien consume que:
  - agenda -> clases_aprobadas_entre(), para descontar lo ocupado de los huecos
  - agenda -> clases_entre(), para el calendario semanal de 1i
  - resenas -> tuvieron_clase(), para exigir que solo resene quien tuvo clase
  - seeds  -> desglosar(), para que los datos de prueba cuadren con el mismo
              calculo que el checkout

A quien le pide datos:
  - perfiles  -> precio_vigente(), reglas_profesor(), condiciones_de_reserva()
                 para cotizar; ficha_resumida() y cabeceras_estudiantes() para
                 la contraparte; sumar_clase_dictada() al completar
  - cuentas   -> datos_basicos_varios(), telefonos_varios()
  - catalogos -> parametros_vigentes(), existe()
  - agenda    -> verificar() y hay_bloqueo_encima() (P3: tolera que no esten)
  - resenas   -> resena_de(), para mi_resena (P3: tolera que no este)
  - pagos     -> retener(), cobrar(), liberar(), reembolsar(), y en que
                 estado esta el cobro de cada clase

Como en P1: estas funciones validan y guardan con flush, pero NO hacen commit.
El commit lo hace la ruta, y por eso crear la clase y retener el cobro van en
una sola transaccion: si el cobro falla, la clase tampoco queda.
"""

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, column, exists, func, or_, select, table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import fechas
from app.enums import Actor, EstadoClase, Modalidad, Rol
from app.errores import ErrorAPI, conflicto, no_es_tuyo, no_existe
from app.modulos.agenda import logica as agenda
from app.modulos.catalogos import logica as catalogos
from app.modulos.clases.modelos import Clase
from app.modulos.cuentas import logica as cuentas
from app.modulos.pagos import logica as pagos
from app.modulos.perfiles import logica as perfiles
from app.modulos.resenas import logica as resenas

# Una clase concreta es presencial u online; "ambas" es una preferencia del
# perfil (ver el CHECK modalidad_concreta de la tabla).
MODALIDADES = (Modalidad.presencial.value, Modalidad.online.value)

# Filas por pagina del calendario (GET /clases).
POR_PAGINA = 50

# Los nombres de materia y etapa, vistos "de lejos": igual que en perfiles,
# las tablas de catalogos se describen a mano por su NOMBRE, con solo id y
# nombre, porque no se puede importar catalogos/modelos.py. Solo para leer.
_CATALOGOS = {
    "materia": table("materia", column("id"), column("nombre")),
    "etapa_educativa": table("etapa_educativa", column("id"), column("nombre")),
}


# ---------------------------------------------------------------------------
# La plata: el UNICO calculo del importe de una clase
# ---------------------------------------------------------------------------

def desglosar(precio_hora: Decimal, duracion_min: int, costo_traslado: Decimal,
              pct_comision: Decimal, pct_iva: Decimal) -> dict:
    """Las cuentas del importe, sin tocar la base. Es la forma de CotizacionOut.

    La usan cotizar() (y por lo tanto crear()) y los seeds: hay UNA sola
    cuenta de plata en todo el sistema. Si alguien la reescribe en otro lado,
    los dos numeros van a diferir y nadie va a saber cual vale.

    Orden del calculo, redondeando a dos decimales (ROUND_HALF_UP) en CADA paso:
      horas     = duracion_min / 60                    (solo para mostrar)
      subtotal  = precio_hora * duracion_min / 60
      comision  = (subtotal + traslado) * pct_comision / 100
      impuesto  = (subtotal + traslado + comision) * pct_iva / 100
      total     = subtotal + traslado + comision + impuesto

    El subtotal sale de los MINUTOS y no de las horas ya redondeadas: 50
    minutos son 0,8333 horas, y con 0,83 una clase de $ 900 la hora saldria
    $ 747 en vez de $ 750.

    Todo con Decimal, NUNCA con float: con float, 1913.18 puede salir
    1913.1800000000003 y el comprobante no cuadra.
    """
    precio = _centesimos(precio_hora)
    traslado = _centesimos(costo_traslado)
    comision_pct = _centesimos(pct_comision)
    iva_pct = _centesimos(pct_iva)

    minutos = Decimal(duracion_min)
    subtotal = _centesimos(precio * minutos / 60)
    comision = _centesimos((subtotal + traslado) * comision_pct / 100)
    impuesto = _centesimos((subtotal + traslado + comision) * iva_pct / 100)
    return {
        "precio_hora": precio,
        "horas": _centesimos(minutos / 60),
        "subtotal": subtotal,
        "costo_traslado": traslado,
        "pct_comision": comision_pct,
        "comision": comision,
        "pct_iva": iva_pct,
        "impuesto": impuesto,
        # Ya son todos de dos decimales: la suma no necesita redondeo.
        "total": subtotal + traslado + comision + impuesto,
    }


def importes_congelados(desglose: dict) -> dict:
    """Las columnas de clase que guardan el desglose, sacadas de desglosar().

    comision y horas no se guardan: salen de las otras. La usan crear() y los
    seeds, asi las dos copian exactamente lo mismo.
    """
    return {
        "precio_hora": desglose["precio_hora"],
        "costo_traslado": desglose["costo_traslado"],
        "pct_comision": desglose["pct_comision"],
        "pct_iva": desglose["pct_iva"],
        "subtotal": desglose["subtotal"],
        "impuesto": desglose["impuesto"],
        "total": desglose["total"],
    }


def cotizar(db: Session, profesor_usuario_id: int, duracion_min: int, modalidad: str, con_traslado: bool) -> dict:
    """El calculo del importe. LA FUNCION MAS PELIGROSA DE DUPLICAR.

    El estimado de 1f y el detalle de 1g salen de aca (y crear() tambien la
    llama). Las cuentas estan en desglosar(); esto junta los datos y valida.

    Errores:
      400 modalidad_invalida   no es presencial ni online
      404 profesor_no_existe   no es profesor, o su ficha no esta publicada
      400 duracion_invalida    no es una de las duraciones que ofrece
      400 sin_precio           no da clase en esa modalidad
    """
    # 1. Una clase concreta es presencial u online.
    if modalidad not in MODALIDADES:
        raise ErrorAPI(400, "modalidad_invalida")

    # 2. Solo se le reserva a una ficha publicada: la pausada o en borrador no
    #    aparece en la busqueda, y tampoco se la puede contratar.
    condiciones = perfiles.condiciones_de_reserva(db, profesor_usuario_id)
    if condiciones is None or not condiciones["publicada"]:
        raise no_existe("profesor")

    # 3. La duracion tiene que ser una de las que ofrece (60, 90, 120...).
    reglas = perfiles.reglas_profesor(db, condiciones["perfil_id"])
    if duracion_min not in reglas["duraciones"]:
        raise ErrorAPI(400, "duracion_invalida")

    # 4. El precio de esa modalidad. None quiere decir que no la ofrece.
    precio = perfiles.precio_vigente(db, profesor_usuario_id, modalidad)
    if precio is None or condiciones["modalidad"] not in (modalidad, Modalidad.ambas.value):
        raise ErrorAPI(400, "sin_precio")

    # 5. Comision e IVA vigentes hoy. La clase los congela al crearse.
    parametros = catalogos.parametros_vigentes(db)

    # 6. El traslado solo se cobra en presencial y si el profesor se traslada.
    traslado = condiciones["costo_traslado"] if _se_traslada(condiciones, modalidad, con_traslado) else Decimal(0)

    return desglosar(precio, duracion_min, traslado,
                     parametros["comision_servicio"], parametros["tasa_iva"])


def crear(db: Session, estudiante_id: int, datos) -> Clase:
    """Crea la clase en pendiente, con los precios congelados y el cobro retenido.

    Es el confirmar de 1g, y toca cuatro modulos. Va todo en UNA transaccion
    (el commit lo hace la ruta): si el cobro falla, la clase no queda creada.

    `datos` es un CrearClaseIn.

    Errores: los de cotizar(), 400 materia_no_existe, 400
    etapa_educativa_no_existe, 409 horario_ocupado, y los de pagos.retener():
    404 tarjeta_no_existe, 402 tarjeta_vencida, 402 cobro_rechazado.
    """
    inicio = fechas.con_zona(datos.inicio)

    # 1. El desglose. cotizar() valida de paso profesor, modalidad, duracion y
    #    precio: si algo de eso esta mal, no tiene sentido seguir.
    desglose = cotizar(db, datos.profesor_id, datos.duracion_min, datos.modalidad, datos.con_traslado)

    # 2. La materia y la etapa tienen que existir: sin esto, la clave foranea
    #    daria un 500 recien al hacer el commit.
    if not catalogos.existe(db, "materia", datos.materia_id):
        raise ErrorAPI(400, "materia_no_existe")
    if datos.etapa_id is not None and not catalogos.existe(db, "etapa_educativa", datos.etapa_id):
        raise ErrorAPI(400, "etapa_educativa_no_existe")

    # 3. agenda.verificar() OTRA VEZ, aunque el checkout ya lo haya chequeado:
    #    entre que abrio la pantalla y confirmo, el hueco se pudo ocupar.
    if not _horario_libre(db, datos.profesor_id, inicio, datos.duracion_min):
        raise conflicto("horario_ocupado")

    # 4. La clase, con TODOS los importes copiados. Si manana el profesor sube
    #    el precio, esta clase sigue valiendo lo mismo.
    condiciones = perfiles.condiciones_de_reserva(db, datos.profesor_id)
    clase = Clase(
        estudiante_id=estudiante_id,
        profesor_id=datos.profesor_id,
        materia_id=datos.materia_id,
        etapa_id=datos.etapa_id,
        tema=_limpio(datos.tema),
        inicio=inicio,
        duracion_min=datos.duracion_min,
        # fin es columna y no se calcula al vuelo: es lo que cruza la
        # restriccion EXCLUDE para detectar superposiciones.
        fin=inicio + timedelta(minutes=datos.duracion_min),
        modalidad=Modalidad(datos.modalidad),
        ubicacion=_ubicacion(db, condiciones, datos.modalidad, datos.con_traslado, estudiante_id),
        estado=EstadoClase.pendiente,
        **importes_congelados(desglose),
    )
    db.add(clase)
    db.flush()  # el cobro necesita clase.id
    if clase.modalidad == Modalidad.online:
        # El enlace de la videollamada es simulado, como el cobro.
        clase.ubicacion = f"https://meet.exonero.test/clase-{clase.id}"

    # 5. El cobro retenido. Si la tarjeta no sirve, esto levanta el error, la
    #    ruta no llega al commit y la sesion se cierra con rollback: la clase
    #    que se acaba de insertar no queda.
    pagos.retener(db, clase.id, datos.tarjeta_id, clase.total, estudiante_id)
    return clase


def resumen(db: Session, clase: Clase) -> dict:
    """La forma de ClaseCreadaOut: {id, estado, total, cobro: {estado}}.

    Es lo que devuelven crear y aprobar: lo justo para que 1g y 1i confirmen
    que paso, sin armar la fila completa del calendario.
    """
    cobro = pagos.cobro_de(db, clase.id)
    return {
        "id": clase.id,
        "estado": clase.estado.value,
        "total": clase.total,
        "cobro": {"estado": cobro["estado"] if cobro else None},
    }


# ---------------------------------------------------------------------------
# Las acciones sobre una clase - 1b y 1i
#
# Todas empiezan igual: buscar la clase (404), ver que quien pide sea parte
# (403) y que este en el estado que la accion necesita (409 estado_invalido).
# La clase se lee con FOR UPDATE: si el profesor aprueba y el alumno cancela
# en el mismo instante, la segunda espera a que termine la primera y ve el
# estado nuevo, en vez de pisarlo.
# ---------------------------------------------------------------------------

def aprobar(db: Session, clase_id: int, profesor_id: int) -> Clase:
    """El profesor acepta. La clase pasa a aprobada y el cobro a cobrado.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido (no esta
    pendiente), 409 horario_ocupado (ya hay otra aprobada encima, o el
    profesor bloqueo ese rato en su agenda).
    """
    clase = _clase_del_profesor(db, clase_id, profesor_id)
    _exigir_estado(clase, EstadoClase.pendiente)

    # 1. Un bloqueo de la agenda encima (P3; mientras no este, no hay bloqueos).
    if _hay_bloqueo(db, profesor_id, clase.inicio, clase.fin):
        raise conflicto("horario_ocupado")

    # 2. LA DEFENSA REAL contra dos clases encimadas: la restriccion EXCLUDE
    #    clase_sin_superposicion de la base, que salta en el UPDATE si ya hay
    #    otra aprobada del mismo profesor que se cruza con esta. Va dentro de
    #    un SAVEPOINT (begin_nested): si salta, se deshace solo el UPDATE y la
    #    sesion sigue sana para responder el 409.
    try:
        with db.begin_nested():
            clase.estado = EstadoClase.aprobada
            db.flush()
    except IntegrityError as error:
        if _restriccion(error) != "clase_sin_superposicion":
            raise
        raise conflicto("horario_ocupado")

    # 3. La plata retenida pasa a cobrada (si ya lo estaba, porque la clase se
    #    reprogramo, cobrar() no hace nada).
    pagos.cobrar(db, clase.id)
    return clase


def rechazar(db: Session, clase_id: int, profesor_id: int) -> None:
    """El profesor rechaza. SE BORRA LA FILA y se libera el cobro.

    La clase rechazada no deja rastro: no es un estado, es una fila que no
    existe mas. El cobro SI queda, con estado liberado y clase_id en NULL,
    porque hubo un movimiento de plata que registrar (y el historial de 1e
    lo muestra como "Solicitud rechazada").

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido.
    """
    clase = _clase_del_profesor(db, clase_id, profesor_id)
    _exigir_estado(clase, EstadoClase.pendiente)
    # ANTES de borrar: despues ya no habria como encontrar el cobro por la clase.
    pagos.liberar(db, clase.id)
    db.delete(clase)
    db.flush()


def cancelar(db: Session, clase_id: int, quien_id: int, motivo: str | None, tareas) -> dict:
    """Cualquiera de las dos partes cancela. NO se borra: cambia de estado.

    Queda en el historial porque el reembolso y la tasa de cancelacion de 1d
    la necesitan. Se puede cancelar una pendiente o una aprobada.

    Que pasa con la plata depende de en que estado este el cobro:
      retenido (todavia pendiente) -> se LIBERA en el momento
      cobrado  (ya aprobada)       -> se encola el REEMBOLSO como BackgroundTask
                                      (`tareas`), para que el cancelar responda
                                      al instante; el cobro pasa a reembolsado
                                      un momento despues

    Devuelve la forma de CancelarOut, con reembolso = {"estado": "liberado" |
    "en_proceso", "importe": total}.

    POLITICA DE CANCELACION, PENDIENTE DE DECIDIR (seccion 11.2 de la
    documentacion): si se reembolsa el total siempre, o si hay un plazo minimo
    (por ejemplo, cancelar con menos de 24 horas). Hoy se devuelve el TOTAL
    siempre, la cancele quien la cancele.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido (ya
    estaba cancelada, dictada o no_asistida).
    """
    clase = _clase(db, clase_id)
    actor = _actor(clase, quien_id)
    _exigir_estado(clase, EstadoClase.pendiente, EstadoClase.aprobada)

    cobro = pagos.cobro_de(db, clase.id) or {}
    if cobro.get("estado") == "retenido":
        pagos.liberar(db, clase.id)
        reembolso = {"estado": "liberado", "importe": cobro["importe"]}
    elif cobro.get("estado") == "cobrado":
        # Corre despues de que la ruta hizo el commit y respondio: para
        # entonces la clase ya figura cancelada. Ver pagos.reembolsar().
        tareas.add_task(pagos.reembolsar, clase.id)
        reembolso = {"estado": "en_proceso", "importe": cobro["importe"]}
    else:
        raise conflicto("estado_invalido")

    clase.estado = EstadoClase.cancelada
    clase.cancelada_por = actor
    clase.motivo = _limpio(motivo)
    db.flush()
    return {"id": clase.id, "estado": clase.estado.value, "cancelada_por": actor.value, "reembolso": reembolso}


def reprogramar(db: Session, clase_id: int, quien_id: int, inicio_nuevo: datetime,
                duracion_min: int | None = None) -> Clase:
    """Cambia la fecha y VUELVE A PENDIENTE, para que el profesor apruebe de nuevo.

    Lo puede pedir cualquiera de las dos partes, sobre una pendiente o una
    aprobada. Los importes NO se recalculan: siguen congelados. Es la misma
    clase movida de lugar, no una nueva. Por eso la duracion no se puede
    cambiar (cambiaria el importe): si viene y es otra, 400.

    Si estaba aprobada, el cobro queda cobrado: al aprobarla de nuevo,
    pagos.cobrar() no hace nada.

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 409 estado_invalido,
    400 duracion_no_modificable, 409 horario_ocupado.
    """
    clase = _clase(db, clase_id)
    _actor(clase, quien_id)
    _exigir_estado(clase, EstadoClase.pendiente, EstadoClase.aprobada)
    if duracion_min is not None and duracion_min != clase.duracion_min:
        raise ErrorAPI(400, "duracion_no_modificable")
    inicio = fechas.con_zona(inicio_nuevo)

    # 1. Primero vuelve a pendiente, y se manda a la base. Asi, si estaba
    #    aprobada, su propio horario viejo deja de contar como ocupado para
    #    agenda.verificar() (que mira las aprobadas): moverla media hora no
    #    choca consigo misma. Si el horario nuevo esta ocupado, el error de
    #    abajo impide el commit y no queda nada cambiado.
    clase.estado = EstadoClase.pendiente
    db.flush()

    # 2. Que el horario nuevo este libre.
    if not _horario_libre(db, clase.profesor_id, inicio, clase.duracion_min):
        raise conflicto("horario_ocupado")

    # 3. Moverla. fin se recalcula: es lo que cruza la restriccion EXCLUDE.
    clase.inicio = inicio
    clase.fin = inicio + timedelta(minutes=clase.duracion_min)
    db.flush()
    return clase


def completar(db: Session, clase_id: int, profesor_id: int, estado: str) -> Clase:
    """El profesor la marca como dictada o no_asistida. Solo una aprobada.

    Si es dictada, suma uno a clases_dictadas de su perfil, y desde ahora
    tuvieron_clase() da True para el par: el alumno ya puede resenarlo.
    El cobro queda cobrado en los dos casos (si el alumno no vino, la clase
    se cobra igual).

    Errores: 404 clase_no_existe, 403 no_es_tuyo, 400 estado_no_permitido
    (`estado` no es dictada ni no_asistida), 409 estado_invalido.
    """
    clase = _clase_del_profesor(db, clase_id, profesor_id)
    if estado not in (EstadoClase.dictada.value, EstadoClase.no_asistida.value):
        raise ErrorAPI(400, "estado_no_permitido")
    _exigir_estado(clase, EstadoClase.aprobada)

    clase.estado = EstadoClase(estado)
    db.flush()
    if clase.estado == EstadoClase.dictada:
        perfiles.sumar_clase_dictada(db, profesor_id)
    return clase


# ---------------------------------------------------------------------------
# Lectura: el calendario, la proxima clase y las solicitudes
# ---------------------------------------------------------------------------

def clases_entre(db: Session, usuario_id: int, desde: datetime | None, hasta: datetime | None,
                 estado: str | None = None, pagina: int | None = None) -> list[dict]:
    """Las clases de un usuario en un rango, sea alumno o profesor, por inicio.

    La misma consulta sirve a 1b, 1d y 1i (GET /clases) y al calendario
    semanal de agenda: el rol del usuario decide si se filtra por
    estudiante_id o por profesor_id.

    Devuelve filas con la forma de ClaseOut (ver armar_clases). desde y hasta
    son instantes con zona, [desde, hasta), y cualquiera puede ser None.
    `pagina` corta de a POR_PAGINA; None las trae todas (para agenda).
    Error: 400 estado_no_permitido si `estado` no es un estado de clase.
    """
    consulta = select(Clase).where(_columna_propia(db, usuario_id) == usuario_id)
    if desde is not None:
        consulta = consulta.where(Clase.inicio >= desde)
    if hasta is not None:
        consulta = consulta.where(Clase.inicio < hasta)
    if estado is not None:
        consulta = consulta.where(Clase.estado == _estado(estado))
    consulta = consulta.order_by(Clase.inicio, Clase.id)
    if pagina is not None:
        consulta = consulta.limit(POR_PAGINA).offset((pagina - 1) * POR_PAGINA)
    return armar_clases(db, db.scalars(consulta).all(), usuario_id)


def proxima(db: Session, usuario_id: int) -> dict | None:
    """La siguiente clase APROBADA que todavia no empezo, o None. 1a, 1b, 1d.

    Es la forma de ProximaClaseOut: una fila del calendario mas la cuenta
    regresiva en minutos (redondeada para abajo).
    """
    ahora = fechas.ahora()
    clase = db.scalar(
        select(Clase)
        .where(
            _columna_propia(db, usuario_id) == usuario_id,
            Clase.estado == EstadoClase.aprobada,
            Clase.inicio > ahora,
        )
        .order_by(Clase.inicio)
        .limit(1)
    )
    if clase is None:
        return None
    fila = armar_clases(db, [clase], usuario_id)[0]
    fila["minutos_restantes"] = int((clase.inicio - ahora).total_seconds() // 60)
    return fila


def solicitudes_pendientes(db: Session, profesor_id: int) -> list[dict]:
    """Las clases pendientes del profesor, por inicio. Es la forma de SolicitudOut.

    Sin expiracion automatica: quedan hasta que el profesor responda. El
    importe ya esta congelado en la clase, no se vuelve a cotizar.
    """
    clases = db.scalars(
        select(Clase)
        .where(Clase.profesor_id == profesor_id, Clase.estado == EstadoClase.pendiente)
        .order_by(Clase.inicio, Clase.id)
    ).all()
    materias = _nombres(db, "materia", [c.materia_id for c in clases])
    alumnos = _contrapartes(db, {c.estudiante_id for c in clases}, set())
    return [
        {
            "id": c.id,
            "inicio": c.inicio,
            "duracion_min": c.duracion_min,
            "materia": materias.get(c.materia_id),
            "tema": c.tema,
            "total": c.total,
            "solicitada_el": c.creado_el,
            "alumno": alumnos[c.estudiante_id],
        }
        for c in clases
    ]


def armar_clases(db: Session, clases: list[Clase], usuario_id: int) -> list[dict]:
    """Varias clases -> filas con la forma de ClaseOut, vistas por `usuario_id`.

    Evita el problema "N+1": los nombres de materia y etapa, el estado de los
    cobros y las contrapartes se piden TODOS JUNTOS, no una consulta por fila.
    Con 50 clases por pagina son unas ocho consultas en total, no 300.

    La contraparte es la otra persona de cada clase: si `usuario_id` es el
    profesor, el alumno (con etapa, centro y telefono, que es lo que muestra
    1d); si no, el profesor (con su puntaje).
    """
    if not clases:
        return []
    materias = _nombres(db, "materia", [c.materia_id for c in clases])
    etapas = _nombres(db, "etapa_educativa", [c.etapa_id for c in clases])
    cobros = pagos.estados_de_cobro(db, [c.id for c in clases])
    contrapartes = _contrapartes(
        db,
        alumnos={c.estudiante_id for c in clases if c.profesor_id == usuario_id},
        profesores={c.profesor_id for c in clases if c.profesor_id != usuario_id},
    )
    return [
        {
            "id": c.id,
            "estado": c.estado.value,
            "inicio": c.inicio,
            "duracion_min": c.duracion_min,
            "materia": materias.get(c.materia_id),
            "etapa": etapas.get(c.etapa_id),
            "tema": c.tema,
            "modalidad": c.modalidad.value,
            "ubicacion": c.ubicacion,
            "total": c.total,
            "cobro_estado": cobros.get(c.id),
            "contraparte": contrapartes[c.estudiante_id if c.profesor_id == usuario_id else c.profesor_id],
        }
        for c in clases
    ]


# ---------------------------------------------------------------------------
# Las personas con las que ya hubo clase - 1b y 1i
# ---------------------------------------------------------------------------

def mis_profesores(db: Session, estudiante_id: int) -> list[dict]:
    """Los profesores con los que el alumno tuvo al menos una clase DICTADA.

    La forma de PersonaConResena. persona trae los datos basicos mas materias
    y precio_hora (para el boton de "volver a reservar").
    """
    return _personas_con_clase(db, estudiante_id, Clase.estudiante_id, Clase.profesor_id, son_profesores=True)


def mis_alumnos(db: Session, profesor_id: int) -> list[dict]:
    """Lo mismo que mis_profesores pero del lado del profesor. persona trae
    solo los datos basicos."""
    return _personas_con_clase(db, profesor_id, Clase.profesor_id, Clase.estudiante_id, son_profesores=False)


# ---------------------------------------------------------------------------
# El panel del profesor - 1d
# ---------------------------------------------------------------------------

def metricas(db: Session, profesor_id: int, periodo: str) -> dict:
    """Los indicadores de 1d del periodo en curso, contra el anterior.

    `periodo` es mes, trimestre o anio, en calendario: octubre contra
    septiembre, este trimestre contra el anterior, este anio contra el pasado
    (ver fechas.rango_periodo). Las clases caen en el periodo por su inicio.

      alumnos_atendidos   distintos alumnos con alguna clase dictada
      horas_dictadas      suma de duracion_min / 60 de las dictadas
      alumnos_recurrentes los que tuvieron 2 o mas clases dictadas
      tasa_cancelacion    canceladas / (canceladas + dictadas), en % (0 a 100)
      variacion           el cambio de cada uno contra el periodo anterior,
                          en %, o None si el anterior fue 0

    Error: 400 periodo_invalido.
    """
    actual = _indicadores(db, profesor_id, *fechas.rango_periodo(periodo))
    anterior = _indicadores(db, profesor_id, *fechas.rango_periodo(periodo, atras=1))
    return {
        **actual,
        "variacion": {clave: _variacion(actual[clave], anterior[clave]) for clave in actual},
    }


def series(db: Session, profesor_id: int, agrupar: str) -> list[dict]:
    """El grafico de reservas de 1d: cuantas clases por tramo y por estado.

    `agrupar` es semana, mes o anio. La ventana son las ultimas 10 semanas, 12
    meses o 5 anios, incluido el actual (ver fechas.ventana). Se agrupa con
    date_trunc de PostgreSQL EN LA ZONA DE MONTEVIDEO: una clase del lunes a
    las 22:00 de aca ya es martes en UTC, y caeria en otra semana.

    Devuelve [{"etiqueta": "AAAA-MM-DD", "cantidad": n, "estado": "dictada"}],
    ordenado por etiqueta. Los tramos sin clases no vienen.
    Error: 400 agrupacion_invalida.
    """
    desde, hasta, unidad = fechas.ventana(agrupar)
    tramo = fechas.tramo(Clase.inicio, unidad)
    filas = db.execute(
        select(tramo.label("tramo"), Clase.estado, func.count().label("cantidad"))
        .where(Clase.profesor_id == profesor_id, Clase.inicio >= desde, Clase.inicio < hasta)
        .group_by(tramo, Clase.estado)
        .order_by(tramo, Clase.estado)
    )
    return [
        {"etiqueta": fechas.etiqueta(f.tramo), "cantidad": f.cantidad, "estado": f.estado.value}
        for f in filas
    ]


# ---------------------------------------------------------------------------
# Lo que consumen los otros modulos
# ---------------------------------------------------------------------------

def clases_aprobadas_entre(db: Session, profesor_id: int, desde: datetime, hasta: datetime) -> list[dict]:
    """Las clases aprobadas de un profesor que se cruzan con [desde, hasta).

    Las descuenta agenda al calcular los huecos libres. Solo aprobadas: las
    pendientes no ocupan el hueco (varias solicitudes sobre el mismo horario
    son legitimas; el profesor elige cual aprueba).

    "Se cruzan" quiere decir que empiezan antes de `hasta` y terminan despues
    de `desde`: una clase de 13 a 15 ocupa parte de un rango que va de 14 a 18.
    Devuelve [{id, inicio, fin, duracion_min, estudiante_id}], por inicio.
    """
    clases = db.scalars(
        select(Clase)
        .where(
            Clase.profesor_id == profesor_id,
            Clase.estado == EstadoClase.aprobada,
            Clase.inicio < hasta,
            Clase.fin > desde,
        )
        .order_by(Clase.inicio)
    )
    return [
        {"id": c.id, "inicio": c.inicio, "fin": c.fin, "duracion_min": c.duracion_min,
         "estudiante_id": c.estudiante_id}
        for c in clases
    ]


def tuvieron_clase(db: Session, a_id: int, b_id: int) -> bool:
    """True si esas dos personas tuvieron al menos una clase dictada.

    En cualquier sentido: no importa cual de los dos es el alumno. Lo usa
    resenas para rechazar con 403 "sin_clases_con_esa_persona" a quien
    intente resenar a alguien con quien nunca tuvo clase.
    """
    return db.scalar(
        select(
            exists().where(
                Clase.estado == EstadoClase.dictada,
                or_(
                    and_(Clase.estudiante_id == a_id, Clase.profesor_id == b_id),
                    and_(Clase.estudiante_id == b_id, Clase.profesor_id == a_id),
                ),
            )
        )
    )


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------

def _horario_libre(db: Session, profesor_id: int, inicio: datetime, duracion_min: int) -> bool:
    """Pregunta a agenda (P3) si el horario sigue libre.

    Mientras P3 no implemente agenda.verificar(), esa funcion levanta
    NotImplementedError. En ese caso se sigue COMO SI ESTUVIERA LIBRE: si no,
    nadie podria reservar nada. No es un agujero: la defensa real contra dos
    clases encimadas es la restriccion EXCLUDE de la base, que salta al
    aprobar (ver aprobar()). Lo que se pierde mientras tanto es el aviso
    temprano (bloqueos, franjas, aviso minimo).

    Cuando P3 la termine, el except deja de activarse solo: no hay que tocar
    nada aca. Es el mismo truco que _contar_no_leidos() en cuentas/rutas.py.
    """
    try:
        return agenda.verificar(db, profesor_id, inicio, duracion_min)["libre"]
    except NotImplementedError:
        return True


def _clase(db: Session, clase_id: int) -> Clase:
    """La clase, bloqueada (FOR UPDATE) hasta el commit. 404 si no existe."""
    clase = db.get(Clase, clase_id, with_for_update=True)
    if clase is None:
        raise no_existe("clase")
    return clase


def _clase_del_profesor(db: Session, clase_id: int, profesor_id: int) -> Clase:
    """Para aprobar, rechazar y completar: solo el profesor de la clase (403)."""
    clase = _clase(db, clase_id)
    if clase.profesor_id != profesor_id:
        raise no_es_tuyo()
    return clase


def _actor(clase: Clase, usuario_id: int) -> Actor:
    """Quien de los dos es `usuario_id` en esta clase. 403 si no es ninguno.

    Es el cancelada_por: sale de quien pide la accion (el token), no del cuerpo.
    """
    if usuario_id == clase.estudiante_id:
        return Actor.estudiante
    if usuario_id == clase.profesor_id:
        return Actor.profesor
    raise no_es_tuyo()


def _exigir_estado(clase: Clase, *estados: EstadoClase) -> None:
    """409 estado_invalido si la clase no esta en uno de esos estados.

    Pasa, por ejemplo, si el alumno cancelo mientras el profesor miraba la
    solicitud: el frontend dice "la clase cambio de estado, recarga".
    """
    if clase.estado not in estados:
        raise conflicto("estado_invalido")


def _hay_bloqueo(db: Session, profesor_id: int, inicio: datetime, fin: datetime) -> bool:
    """Pregunta a agenda (P3) si el profesor bloqueo ese rato.

    Igual que _horario_libre(): mientras P3 no implemente
    agenda.hay_bloqueo_encima(), levanta NotImplementedError y se sigue como
    si no hubiera bloqueos (todavia no hay como cargarlos). Cuando este, se
    usa sola. OJO: agenda trabaja con el id del PERFIL, no del usuario.
    """
    try:
        perfil_id = perfiles.condiciones_de_reserva(db, profesor_id)["perfil_id"]
        return agenda.hay_bloqueo_encima(db, perfil_id, inicio, fin)
    except NotImplementedError:
        return False


def _restriccion(error: IntegrityError) -> str | None:
    """El nombre de la restriccion que hizo fallar el INSERT o el UPDATE.

    Para distinguir la EXCLUDE de la superposicion de cualquier otro error de
    integridad, que no es un 409 sino un error de verdad.
    """
    diagnostico = getattr(error.orig, "diag", None)
    return getattr(diagnostico, "constraint_name", None)


def _columna_propia(db: Session, usuario_id: int):
    """Clase.profesor_id o Clase.estudiante_id, segun el rol del usuario.

    Es lo que hace que el calendario del alumno y el del profesor sean la
    misma consulta. El usuario ya esta cargado (lo resolvio el token), asi que
    obtener_usuario() no vuelve a la base.
    """
    usuario = cuentas.obtener_usuario(db, usuario_id)
    if usuario is not None and usuario.rol == Rol.profesor:
        return Clase.profesor_id
    return Clase.estudiante_id


def _estado(estado: str) -> EstadoClase:
    """El texto de un filtro -> EstadoClase. 400 estado_no_permitido si no es uno."""
    try:
        return EstadoClase(estado)
    except ValueError:
        raise ErrorAPI(400, "estado_no_permitido")


def _nombres(db: Session, catalogo: str, ids) -> dict[int, str]:
    """{id: nombre} para esos ids del catalogo, en UNA sola consulta."""
    ids = {i for i in ids if i is not None}
    if not ids:
        return {}
    t = _CATALOGOS[catalogo]
    return {fila.id: fila.nombre for fila in db.execute(select(t.c.id, t.c.nombre).where(t.c.id.in_(ids)))}


def _contrapartes(db: Session, alumnos: set[int], profesores: set[int]) -> dict[int, dict]:
    """{usuario_id: Contraparte} de varias personas, con pocas consultas.

    Los alumnos llevan etapa, centro, telefono y su puntaje (lo que ve el
    profesor en 1d y en las solicitudes de 1i). Los profesores llevan su
    puntaje y la cantidad de resenas (lo que ve el alumno en 1b).
    """
    personas = cuentas.datos_basicos_varios(db, [*alumnos, *profesores])
    resultado = {
        uid: {
            "id": uid,
            "nombre": p["nombre"],
            "apellido": p["apellido"],
            "foto_base64": p["foto_base64"],
        }
        for uid, p in personas.items()
    }
    if alumnos:
        telefonos = cuentas.telefonos_varios(db, list(alumnos))
        cabeceras = perfiles.cabeceras_estudiantes(db, list(alumnos))
        for uid in alumnos:
            cabecera = cabeceras.get(uid, {})
            resultado[uid].update(
                etapa=cabecera.get("etapa"),
                centro=cabecera.get("centro"),
                telefono=telefonos.get(uid),
                puntaje_promedio=cabecera.get("puntaje_promedio"),
                cantidad_resenas=cabecera.get("cantidad_resenas"),
            )
    if profesores:
        for ficha in perfiles.ficha_resumida(db, list(profesores)):
            resultado[ficha["id"]].update(
                puntaje_promedio=ficha["puntaje_promedio"],
                cantidad_resenas=ficha["cantidad_resenas"],
            )
    return resultado


def _personas_con_clase(db: Session, yo_id: int, columna_yo, columna_otro, son_profesores: bool) -> list[dict]:
    """Lo comun a mis_profesores y mis_alumnos: personas con clases DICTADAS.

    Una consulta agrupa por la otra persona (cuantas dictadas y la ultima), y
    despues se completan los datos de todas juntas. La que tuvo clase mas
    recientemente va primero.
    """
    ultima = func.max(Clase.inicio)
    filas = db.execute(
        select(columna_otro.label("persona_id"), func.count().label("cantidad"), ultima.label("ultima"))
        .where(columna_yo == yo_id, Clase.estado == EstadoClase.dictada)
        .group_by(columna_otro)
        .order_by(ultima.desc())
    ).all()
    ids = [f.persona_id for f in filas]
    personas = cuentas.datos_basicos_varios(db, ids)
    fichas = {f["id"]: f for f in perfiles.ficha_resumida(db, ids)} if son_profesores else {}
    mis_resenas = _mis_resenas(db, yo_id, ids)

    resultado = []
    for fila in filas:
        persona = dict(personas[fila.persona_id])
        if fila.persona_id in fichas:
            persona["materias"] = fichas[fila.persona_id]["materias"]
            persona["precio_hora"] = fichas[fila.persona_id]["precio_hora"]
        resultado.append({
            "persona": persona,
            "cantidad_clases": fila.cantidad,
            "ultima_clase": fila.ultima,
            "mi_resena": mis_resenas.get(fila.persona_id),
        })
    return resultado


def _mis_resenas(db: Session, autor_id: int, destinatarios: list[int]) -> dict[int, dict]:
    """{destinatario: la resena que `autor_id` le dejo}, para mi_resena.

    resenas.resena_de() es de P3. Mientras no la implemente, levanta
    NotImplementedError y mi_resena viene en null para todos: la pantalla
    muestra el boton de resenar, que es lo que corresponde si no hay resenas.
    Cuando P3 la termine, esto empieza a usarla sin tocar nada (el mismo truco
    que _contar_no_leidos() en cuentas/rutas.py).
    """
    resultado = {}
    try:
        for destinatario in destinatarios:
            resena = resenas.resena_de(db, autor_id, destinatario)
            if resena is not None:
                resultado[destinatario] = resena
    except NotImplementedError:
        return {}
    return resultado


def _indicadores(db: Session, profesor_id: int, desde: datetime, hasta: datetime) -> dict:
    """Los cuatro numeros de 1d para un rango, con dos consultas."""
    # Por alumno: cuantas dictadas tuvo y cuantos minutos sumaron.
    por_alumno = db.execute(
        select(Clase.estudiante_id, func.count().label("cantidad"), func.sum(Clase.duracion_min).label("minutos"))
        .where(
            Clase.profesor_id == profesor_id,
            Clase.estado == EstadoClase.dictada,
            Clase.inicio >= desde,
            Clase.inicio < hasta,
        )
        .group_by(Clase.estudiante_id)
    ).all()
    canceladas = db.scalar(
        select(func.count()).select_from(Clase).where(
            Clase.profesor_id == profesor_id,
            Clase.estado == EstadoClase.cancelada,
            Clase.inicio >= desde,
            Clase.inicio < hasta,
        )
    )
    dictadas = sum(f.cantidad for f in por_alumno)
    minutos = sum(f.minutos for f in por_alumno)
    base = canceladas + dictadas
    return {
        "alumnos_atendidos": len(por_alumno),
        "horas_dictadas": _centesimos(Decimal(minutos) / 60),
        "alumnos_recurrentes": sum(1 for f in por_alumno if f.cantidad >= 2),
        "tasa_cancelacion": _un_decimal(Decimal(canceladas) * 100 / base) if base else Decimal("0.0"),
    }


def _variacion(actual, anterior) -> float | None:
    """Cuanto cambio, en porcentaje con un decimal. None si el anterior fue 0.

    Es un porcentaje y no plata: va como numero (float) en el JSON.
    """
    if not anterior:
        return None
    return float(_un_decimal((Decimal(actual) - Decimal(anterior)) * 100 / Decimal(anterior)))


def _se_traslada(condiciones: dict, modalidad: str, con_traslado: bool) -> bool:
    """True si el profesor va a la casa del alumno, y por lo tanto cobra el traslado.

    Solo en presencial (en online no hay a donde ir) y solo si el profesor se
    traslada: si el alumno lo pide y el profesor no va, se ignora.
    """
    return modalidad == Modalidad.presencial.value and con_traslado and condiciones["hace_traslado"]


def _ubicacion(db: Session, condiciones: dict, modalidad: str, con_traslado: bool,
               estudiante_id: int) -> str | None:
    """Donde es la clase: la casa del alumno, el espacio del profesor, o nada.

    En online se completa despues, con el enlace (necesita el id de la clase).
    El profesor que SOLO va a domicilio da la clase en la casa del alumno
    aunque no se haya marcado el traslado.
    """
    if modalidad == Modalidad.online.value:
        return None
    if _se_traslada(condiciones, modalidad, con_traslado) or condiciones["lugar_clase"] == "a_domicilio":
        return perfiles.direccion_estudiante(db, estudiante_id)
    return condiciones["direccion_espacio"]


def _centesimos(valor) -> Decimal:
    """Redondea a dos decimales, ROUND_HALF_UP (el 0,005 sube, como en la escuela).

    Acepta int o Decimal. Si llegara un float, pasa por str() para no arrastrar
    la representacion binaria (Decimal(0.1) es 0.1000000000000000055...).
    """
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _un_decimal(valor: Decimal) -> Decimal:
    """Los porcentajes de 1d van con un decimal: 12,5 %."""
    return valor.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _limpio(texto: str | None) -> str | None:
    """Saca los espacios de los costados. Un texto vacio se guarda como NULL."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None
