"""Funciones publicas del modulo resenas - dueno P3.

resenas es el UNICO modulo que escribe puntaje_promedio y cantidad_resenas en
los perfiles. Si alguien mas los toca, los numeros dejan de coincidir con la
tabla de resenas y no hay forma de saber cual esta bien.

Quien consume que:
  - clases -> resena_de(), para el mi_resena de /mis-profesores y /mis-alumnos

A quien le pide datos:
  - clases   -> tuvieron_clase(), para exigir que solo resene quien tuvo clase
  - perfiles -> escribir_puntaje(), para guardar el promedio recalculado
  - cuentas  -> obtener_usuario(), para saber si el destinatario existe

EL ANONIMATO. La tabla guarda el autor (hace falta para la regla de una resena
por persona y para poder editarla), pero NINGUNA funcion de aca lo devuelve,
salvo resena_de(), que es la propia: quien pregunta es el autor.

Como clases importa resenas y resenas importa clases, las dos se importan como
modulo y solo se usan adentro de las funciones (igual que agenda y clases).
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import fechas
from app.enums import Rol, SentidoResena
from app.errores import ErrorAPI, conflicto, no_existe
from app.modulos.clases import logica as clases
from app.modulos.cuentas import logica as cuentas
from app.modulos.perfiles import logica as perfiles
from app.modulos.resenas.modelos import Resena

POR_PAGINA = 10
ORDENES = ("recientes", "puntaje")


def dejar_o_editar(db: Session, autor_id: int, autor_rol: str, datos, crear: bool) -> dict:
    """Crea la resena (crear=True, POST) o edita la que ya habia dejado (PUT).

    El sentido sale del rol del token, no del cuerpo: si el autor es
    estudiante, es alumno_a_profesor; si es profesor, profesor_a_alumno.

    Errores:
      403 sin_clases_con_esa_persona  nunca tuvieron una clase dictada
      409 ya_resenado                 POST pero ya existe (que use PUT)
      404 resena_no_existe            PUT pero todavia no hay ninguna

    Devuelve la forma de ResenaOut.
    """
    if not clases.tuvieron_clase(db, autor_id, datos.destinatario_id):
        raise ErrorAPI(403, "sin_clases_con_esa_persona")

    resena = _de(db, autor_id, datos.destinatario_id)
    if crear and resena is not None:
        raise conflicto("ya_resenado")
    if not crear and resena is None:
        raise no_existe("resena")

    if resena is None:
        sentido = SentidoResena.alumno_a_profesor if Rol(autor_rol) == Rol.estudiante else SentidoResena.profesor_a_alumno
        resena = Resena(autor_id=autor_id, destinatario_id=datos.destinatario_id, sentido=sentido,
                        puntaje=datos.puntaje)
        db.add(resena)
    resena.puntaje = datos.puntaje
    resena.texto = _limpio(datos.texto)
    db.flush()

    # SIEMPRE, si no el promedio que muestran busqueda y las solicitudes queda viejo.
    recalcular(db, datos.destinatario_id)
    return _a_dict(resena)


def recalcular(db: Session, usuario_id: int) -> None:
    """Recalcula el promedio y la cantidad, y los escribe en el perfil.

    Se llama despues de cada alta o edicion (y desde los seeds). Es la unica
    forma en que puntaje_promedio y cantidad_resenas cambian de valor.
    perfiles se fija solo si el perfil es de estudiante o de profesor.
    """
    promedio, cantidad = db.execute(
        select(func.avg(Resena.puntaje), func.count()).where(Resena.destinatario_id == usuario_id)
    ).one()
    perfiles.escribir_puntaje(db, usuario_id, _dos_decimales(promedio or 0), cantidad)


def resumen(db: Session, usuario_id: int) -> dict:
    """Promedio, cantidad y distribucion por estrella. Forma de ResumenResenasOut.

    Sirve igual para un profesor y para un alumno. La distribucion trae las
    cinco estrellas SIEMPRE, con cero las que no aparecieron: el grafico de
    barras las necesita todas.

    Error: 404 usuario_no_existe.
    """
    if cuentas.obtener_usuario(db, usuario_id) is None:
        raise no_existe("usuario")
    filas = db.execute(
        select(Resena.puntaje, func.count())
        .where(Resena.destinatario_id == usuario_id)
        .group_by(Resena.puntaje)
    ).all()
    distribucion = {str(estrella): 0 for estrella in range(5, 0, -1)}
    for estrella, cuantas in filas:
        distribucion[str(estrella)] = cuantas
    total = sum(distribucion.values())
    suma = sum(int(estrella) * cuantas for estrella, cuantas in distribucion.items())
    return {
        "total": total,
        "promedio": float(_dos_decimales(Decimal(suma) / total)) if total else 0.0,
        "distribucion": distribucion,
    }


def pagina(db: Session, usuario_id: int, orden: str, numero: int) -> dict:
    """El resumen mas una pagina de resenas recibidas. Forma de PaginaResenasOut.

    `orden`: recientes (la mas nueva primero) o puntaje (la mas alta primero).
    SIN AUTOR: cada resena es solo puntaje, texto y fecha.

    Errores: 400 orden_invalido, 404 usuario_no_existe.
    """
    if orden not in ORDENES:
        raise ErrorAPI(400, "orden_invalido")
    datos = resumen(db, usuario_id)
    criterio = (
        (Resena.creado_el.desc(), Resena.id.desc())
        if orden == "recientes"
        else (Resena.puntaje.desc(), Resena.creado_el.desc(), Resena.id.desc())
    )
    resenas = db.scalars(
        select(Resena)
        .where(Resena.destinatario_id == usuario_id)
        .order_by(*criterio)
        .limit(POR_PAGINA)
        .offset((numero - 1) * POR_PAGINA)
    )
    datos["resenas"] = [_a_dict(r) for r in resenas]
    return datos


def resena_de(db: Session, autor_id: int, destinatario_id: int) -> dict | None:
    """La resena que una persona le dejo a otra, o None.

    Es el campo mi_resena de GET /clases/mis-profesores y /mis-alumnos. Aca SI
    se devuelve, porque es la propia: el autor puede ver y editar la suya.
    """
    resena = _de(db, autor_id, destinatario_id)
    return _a_dict(resena) if resena else None


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------

def _de(db: Session, autor_id: int, destinatario_id: int) -> Resena | None:
    return db.scalar(
        select(Resena).where(Resena.autor_id == autor_id, Resena.destinatario_id == destinatario_id)
    )


def _a_dict(resena: Resena) -> dict:
    """Una resena para la API: sin autor, nunca."""
    return {
        "puntaje": resena.puntaje,
        "texto": resena.texto,
        "fecha": resena.creado_el.astimezone(fechas.ZONA).date(),
    }


def _dos_decimales(valor) -> Decimal:
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _limpio(texto: str | None) -> str | None:
    """Sin espacios de mas, y None si quedo vacio."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None
