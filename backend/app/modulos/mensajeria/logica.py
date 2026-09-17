"""Funciones publicas del modulo mensajeria - dueno P3.

Quien consume que:
  - cuentas -> contar_no_leidos(), para el contador de GET /usuarios/yo
"""

from sqlalchemy.orm import Session


def contar_no_leidos(db: Session, usuario_id: int) -> int:
    """Cuantos mensajes sin leer tiene una persona, en todos sus hilos.

    Lo llama cuentas para armar GET /usuarios/yo, y tambien la ruta
    GET /mensajes/no-leidos, que el frontend consulta cada diez segundos.

    Cuenta los mensajes con leido_el IS NULL cuyo autor NO sea esta persona.

    TODO (P3): implementar. Tiene que ser barato: se llama muchisimo. Usa el
    indice parcial ix_mensaje_sin_leer.
    """
    raise NotImplementedError("P3 - mensajeria: contar mensajes no leidos")


def obtener_o_crear_hilo(db: Session, estudiante_id: int, profesor_id: int) -> object:
    """Devuelve el hilo entre esas dos personas, y lo crea si no existia.

    Es lo que hace el boton de contactar de 1f. Gracias al UNIQUE
    (estudiante_id, profesor_id), entrar diez veces desde la ficha no crea
    diez hilos.

    TODO (P3): implementar. Ojo con la carrera: si dos requests entran a la vez
    el UNIQUE tira IntegrityError; capturarlo y devolver el hilo que gano.
    """
    raise NotImplementedError("P3 - mensajeria: obtener o crear el hilo")


def marcar_leidos(db: Session, hilo_id: int, usuario_id: int) -> None:
    """Marca como leidos todos los mensajes del hilo que no escribio esta persona.

    Se llama DENTRO del GET que trae los mensajes, no como accion aparte:
    abrir el hilo es leerlo.

    TODO (P3): implementar. Un solo UPDATE con WHERE leido_el IS NULL.
    """
    raise NotImplementedError("P3 - mensajeria: marcar los mensajes como leidos")
