"""Funciones publicas del modulo agenda - dueno P3.

agenda responde una sola pregunta, pero es la mas cara del sistema: cuando
tiene lugar este profesor.

Quien consume que:
  - busqueda -> filtrar_con_hueco(), para el filtro de disponibilidad de 1c
  - busqueda -> primera_hora_libre(), para la columna de resultados y el carrusel
  - clases   -> verificar(), antes de insertar una clase

A quien le pide datos:
  - perfiles -> reglas_profesor(), para saber descanso, tope y aviso minimo
  - clases   -> clases_aprobadas_entre(), para descontar lo que ya esta ocupado
"""

from datetime import date, datetime

from sqlalchemy.orm import Session


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

    TODO (P3): implementar. Ojo con la zona horaria: las franjas son `time`
    sin zona y las clases son timestamptz. Hay que combinarlas en
    America/Montevideo antes de comparar, o los huecos salen corridos.
    """
    raise NotImplementedError("P3 - agenda: calcular los huecos libres")


def verificar(db: Session, profesor_usuario_id: int, inicio: datetime, duracion_min: int) -> dict:
    """Dice si un horario puntual sigue libre, y si no, por que.

    Se llama DOS VECES en el flujo de reserva: al elegir el horario en 1f y de
    nuevo al apretar confirmar en 1g, porque entre una cosa y la otra el hueco
    se pudo ocupar. Y una tercera vez cuando el profesor reprograma desde 1i.

    Devuelve {"libre": True} o {"libre": False, "motivo": "..."} con uno de:
    ocupado, bloqueado, fuera_de_franja, aviso_minimo, tope_diario.

    TODO (P3): implementar. Devolver el motivo concreto y no solo False: el
    frontend muestra mensajes distintos para cada caso.
    """
    raise NotImplementedError("P3 - agenda: verificar un horario puntual")


def filtrar_con_hueco(db: Session, ids_profesor: list[int], dia: int | None, franja: str | None) -> list[int]:
    """De una lista de profesores, cuales tienen hueco real ese dia y esa franja.

    Lo llama busqueda POR DENTRO: no es una ruta HTTP. Es el filtro de
    disponibilidad de 1c.

    `franja` es manana, tarde, noche o fin_de_semana.

    TODO (P3): implementar. Recibe la lista YA RECORTADA por los otros filtros;
    no recorrer todos los profesores de la base.
    """
    raise NotImplementedError("P3 - agenda: filtrar profesores con hueco")


def primera_hora_libre(db: Session, ids_profesor: list[int]) -> dict[int, datetime]:
    """La proxima hora libre de cada profesor, en UNA consulta.

    Es la columna "proxima_hora_libre" de los resultados de 1c y del carrusel
    de 1a. Devuelve {usuario_id: datetime}.

    TODO (P3): implementar. En lote, no uno por uno: esto se llama con veinte
    profesores por pagina de resultados.
    """
    raise NotImplementedError("P3 - agenda: primera hora libre en lote")


def hay_bloqueo_encima(db: Session, perfil_profesor_id: int, inicio: datetime, fin: datetime) -> bool:
    """True si un rango pisa algun bloqueo.

    Lo usa la propia agenda al crear un bloqueo nuevo y clases al aprobar.

    TODO (P3): implementar.
    """
    raise NotImplementedError("P3 - agenda: detectar bloqueos superpuestos")
