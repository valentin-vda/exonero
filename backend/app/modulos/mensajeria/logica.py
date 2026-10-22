"""Funciones publicas del modulo mensajeria - dueno P3.

Chat directo entre un alumno y un profesor: una conversacion (hilo) por par,
sin contexto de clase y sin reservar desde ahi.

Quien consume que:
  - cuentas -> contar_no_leidos(), para el contador de GET /usuarios/yo

A quien le pide datos:
  - cuentas  -> obtener_usuario() y datos_basicos_varios(), para la otra persona
  - perfiles -> ficha_resumida() (materias del profe) y cabeceras_estudiantes()
                (etapa y centro del alumno), para la cabecera de cada hilo

Para saber si un profesor puede escribirle a un alumno ("tienen alguna
clase") se lee la tabla clase DE LEJOS, con table()/column(): solo lectura,
sin importar el modelo de clases (es el patron de la seccion 2 de la
documentacion).

Como en el resto: estas funciones validan y guardan con flush, pero NO hacen
commit. El commit lo hace la ruta.
"""

import unicodedata

from sqlalchemy import column, exists, func, or_, select, table, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import fechas
from app.enums import Rol
from app.errores import ErrorAPI, no_es_tuyo, no_existe
from app.modulos.cuentas import logica as cuentas
from app.modulos.mensajeria.modelos import Hilo, Mensaje
from app.modulos.perfiles import logica as perfiles

# La tabla clase, vista de lejos: solo las columnas que hacen falta.
_clase = table("clase", column("estudiante_id"), column("profesor_id"))

LIMITE_MAXIMO = 100


def contar_no_leidos(db: Session, usuario_id: int) -> int:
    """Cuantos mensajes sin leer tiene una persona, en todos sus hilos.

    Lo llama cuentas para armar GET /usuarios/yo, y tambien la ruta
    GET /mensajes/no-leidos, que el frontend consulta cada diez segundos.

    Cuenta los mensajes con leido_el IS NULL cuyo autor NO sea esta persona,
    en los hilos donde participa. Un solo COUNT, que usa el indice parcial
    ix_mensaje_sin_leer.
    """
    return db.scalar(
        select(func.count())
        .select_from(Mensaje)
        .join(Hilo, Hilo.id == Mensaje.hilo_id)
        .where(
            or_(Hilo.estudiante_id == usuario_id, Hilo.profesor_id == usuario_id),
            Mensaje.autor_id != usuario_id,
            Mensaje.leido_el.is_(None),
        )
    )


def obtener_o_crear_hilo(db: Session, yo, otro_id: int) -> tuple[Hilo, bool]:
    """Devuelve el hilo entre yo y otra persona, y lo crea si no existia.

    Devuelve (hilo, creado). Gracias al UNIQUE (estudiante_id, profesor_id),
    entrar diez veces desde la ficha no crea diez hilos.

    Quien puede abrirlo:
      - el alumno, con cualquier profesor (es el "Enviar mensaje" de 1f)
      - el profesor, solo con un alumno que tenga alguna clase con el (el
        "Mensaje" de la proxima clase en 1d). Asi un profe no puede escribirle
        a cualquier alumno de la plataforma.

    Errores: 404 profesor_no_existe, 404 estudiante_no_existe,
             403 sin_clases_con_esa_persona.
    """
    otro = cuentas.obtener_usuario(db, otro_id)
    if yo.rol == Rol.estudiante:
        if otro is None or otro.rol != Rol.profesor:
            raise no_existe("profesor")
        estudiante_id, profesor_id = yo.id, otro.id
    else:
        if otro is None or otro.rol != Rol.estudiante:
            raise no_existe("estudiante")
        if not _tienen_clase(db, otro.id, yo.id):
            raise ErrorAPI(403, "sin_clases_con_esa_persona")
        estudiante_id, profesor_id = otro.id, yo.id

    hilo = _hilo_entre(db, estudiante_id, profesor_id)
    if hilo is not None:
        return hilo, False

    # Si dos requests entran a la vez, la segunda choca con el UNIQUE. Va en un
    # SAVEPOINT: si salta, se deshace solo el INSERT y se devuelve el que gano.
    try:
        with db.begin_nested():
            hilo = Hilo(estudiante_id=estudiante_id, profesor_id=profesor_id)
            db.add(hilo)
            db.flush()
        return hilo, True
    except IntegrityError:
        return _hilo_entre(db, estudiante_id, profesor_id), False


def bandeja(db: Session, usuario_id: int, q: str | None = None) -> list[dict]:
    """La bandeja de 1h: los hilos de la persona, el de actividad mas reciente primero.

    Ordena por ultimo_mensaje_el (la columna desnormalizada del hilo), no por
    un MAX sobre mensaje. Los hilos sin mensajes (recien abiertos) van al final.

    Sin N+1: el ultimo mensaje de cada hilo sale de UNA consulta (DISTINCT ON),
    los no leidos de un GROUP BY, y los datos de la otra persona en lote. Son
    unas seis consultas, tenga los hilos que tenga.

    `q` filtra por el nombre de la otra persona, sin importar mayusculas ni
    tildes ("lucia" encuentra a "Lucía").

    Devuelve filas con la forma de HiloOut.
    """
    hilos = db.scalars(
        select(Hilo)
        .where(or_(Hilo.estudiante_id == usuario_id, Hilo.profesor_id == usuario_id))
        .order_by(Hilo.ultimo_mensaje_el.desc().nulls_last(), Hilo.id.desc())
    ).all()
    if not hilos:
        return []
    ids = [h.id for h in hilos]

    ultimos = dict(db.execute(
        select(Mensaje.hilo_id, Mensaje.contenido)
        .where(Mensaje.hilo_id.in_(ids))
        .distinct(Mensaje.hilo_id)
        .order_by(Mensaje.hilo_id, Mensaje.enviado_el.desc(), Mensaje.id.desc())
    ).all())
    no_leidos = dict(db.execute(
        select(Mensaje.hilo_id, func.count())
        .where(Mensaje.hilo_id.in_(ids), Mensaje.autor_id != usuario_id, Mensaje.leido_el.is_(None))
        .group_by(Mensaje.hilo_id)
    ).all())
    contrapartes = _contrapartes(db, [_otro(h, usuario_id) for h in hilos])

    filas = [
        {
            "id": h.id,
            "contraparte": contrapartes[_otro(h, usuario_id)],
            "ultimo_mensaje": ultimos.get(h.id),
            "ultimo_mensaje_el": h.ultimo_mensaje_el,
            "no_leidos": no_leidos.get(h.id, 0),
        }
        for h in hilos
    ]
    if q and q.strip():
        buscado = _sin_tildes(q)
        filas = [
            f for f in filas
            if buscado in _sin_tildes(f"{f['contraparte']['nombre']} {f['contraparte'].get('apellido') or ''}")
        ]
    return filas


def hilo_propio(db: Session, hilo_id: int, usuario_id: int) -> Hilo:
    """El hilo, si esta persona es parte. 404 hilo_no_existe, 403 no_es_tuyo."""
    hilo = db.get(Hilo, hilo_id)
    if hilo is None:
        raise no_existe("hilo")
    if usuario_id not in (hilo.estudiante_id, hilo.profesor_id):
        raise no_es_tuyo()
    return hilo


def fila_de_hilo(db: Session, hilo: Hilo, usuario_id: int) -> dict:
    """Un solo hilo con la forma de HiloOut (lo que devuelve POST /mensajes/hilos)."""
    return next(f for f in bandeja(db, usuario_id) if f["id"] == hilo.id)


def mensajes(db: Session, hilo: Hilo, usuario_id: int, antes: int | None, limite: int) -> list[dict]:
    """Una pagina del historial, y marca el hilo como leido. Forma de MensajeOut.

    Paginado hacia atras: trae los `limite` mensajes anteriores al mensaje
    `antes` (el id del mas viejo que ya tiene el frontend), o los ultimos si
    no viene. La pagina vuelve en orden CRONOLOGICO (el mas viejo primero),
    que es como se dibuja el chat: el frontend la pega arriba de lo que ya
    tiene sin dar vuelta nada.

    Abrir el hilo es leerlo: marca como leidos los mensajes del otro, en el
    mismo llamado. No hay una accion aparte.
    """
    limite = max(1, min(limite, LIMITE_MAXIMO))
    consulta = select(Mensaje).where(Mensaje.hilo_id == hilo.id)
    if antes is not None:
        consulta = consulta.where(Mensaje.id < antes)
    pagina = db.scalars(consulta.order_by(Mensaje.enviado_el.desc(), Mensaje.id.desc()).limit(limite)).all()
    marcar_leidos(db, hilo.id, usuario_id)
    return [_a_dict(m) for m in reversed(pagina)]


def marcar_leidos(db: Session, hilo_id: int, usuario_id: int) -> None:
    """Marca como leidos todos los mensajes del hilo que no escribio esta persona.

    Se llama DENTRO del GET que trae los mensajes, no como accion aparte:
    abrir el hilo es leerlo. Un solo UPDATE con WHERE leido_el IS NULL.
    """
    db.execute(
        update(Mensaje)
        .where(Mensaje.hilo_id == hilo_id, Mensaje.autor_id != usuario_id, Mensaje.leido_el.is_(None))
        .values(leido_el=fechas.ahora())
    )
    db.flush()


def enviar(db: Session, hilo: Hilo, usuario_id: int, texto: str) -> dict:
    """Agrega un mensaje al hilo. Forma de MensajeOut.

    Inserta el mensaje Y actualiza hilo.ultimo_mensaje_el en el mismo flush:
    si no, la bandeja se desordena.

    Error: 400 mensaje_vacio (solo espacios).
    """
    texto = (texto or "").strip()
    if not texto:
        raise ErrorAPI(400, "mensaje_vacio")
    ahora = fechas.ahora()
    mensaje = Mensaje(hilo_id=hilo.id, autor_id=usuario_id, contenido=texto, enviado_el=ahora)
    db.add(mensaje)
    hilo.ultimo_mensaje_el = ahora
    db.flush()
    return _a_dict(mensaje)


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------

def _hilo_entre(db: Session, estudiante_id: int, profesor_id: int) -> Hilo | None:
    return db.scalar(select(Hilo).where(Hilo.estudiante_id == estudiante_id, Hilo.profesor_id == profesor_id))


def _tienen_clase(db: Session, estudiante_id: int, profesor_id: int) -> bool:
    """True si hay al menos una clase entre los dos, en cualquier estado."""
    return db.scalar(select(exists().where(
        _clase.c.estudiante_id == estudiante_id, _clase.c.profesor_id == profesor_id,
    )))


def _otro(hilo: Hilo, usuario_id: int) -> int:
    return hilo.profesor_id if hilo.estudiante_id == usuario_id else hilo.estudiante_id


def _contrapartes(db: Session, ids: list[int]) -> dict[int, dict]:
    """La otra persona de cada hilo, en lote. Forma de ContraparteHilo.

    Si es profesor, con sus materias (la cabecera de 1h dice "Matematica ·
    Fisica"); si es alumno, con su etapa y centro.
    """
    basicos = cuentas.datos_basicos_varios(db, ids)
    profes = [i for i, d in basicos.items() if d["rol"] == Rol.profesor.value]
    materias = {f["id"]: f["materias"] for f in perfiles.ficha_resumida(db, profes)}
    alumnos = perfiles.cabeceras_estudiantes(db, [i for i in basicos if i not in materias])
    resultado = {}
    for i, datos in basicos.items():
        fila = {k: datos[k] for k in ("id", "nombre", "apellido", "foto_base64", "rol")}
        fila["materias"] = materias.get(i, [])
        fila["etapa"] = alumnos.get(i, {}).get("etapa")
        fila["centro"] = alumnos.get(i, {}).get("centro")
        resultado[i] = fila
    return resultado


def _a_dict(mensaje: Mensaje) -> dict:
    return {
        "id": mensaje.id,
        "autor_id": mensaje.autor_id,
        "contenido": mensaje.contenido,
        "enviado_el": mensaje.enviado_el,
    }


def _sin_tildes(texto: str) -> str:
    """'Lucía' -> 'lucia', para buscar sin que importen mayusculas ni tildes."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn"
    ).strip()
