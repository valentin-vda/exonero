"""Funciones publicas del modulo busqueda - dueno P2.

busqueda es casi todo lectura: no escribe nada y no lo consume ningun otro
modulo. Al reves: consume perfiles, catalogos y agenda.

A quien le pide datos:
  - perfiles  -> ficha_resumida(), para completar las filas de resultados
  - catalogos -> centroide_barrio(), para calcular distancias
  - agenda    -> filtrar_con_hueco(), para el filtro de disponibilidad
"""

from sqlalchemy.orm import Session


def buscar(db: Session, filtros) -> dict:
    """El corazon de 1c: los nueve filtros combinables, ordenados y paginados.

    Arma UNA consulta con todos los filtros que vinieron. El orden importa por
    rendimiento: primero los que cortan mas (materia y barrio, que tienen
    indice) y al final el de disponibilidad, que es el mas caro.

    TODO (P2): implementar.
      1. Partir de perfil_profesor con estado_ficha = publicada. Siempre.
      2. Aplicar los filtros que vinieron:
         materia  -> join profesor_materia
         etapa    -> join profesor_etapa
         idioma   -> join profesor_idioma
         barrio   -> barrio_id propio O join profesor_zona (se traslada ahi)
         centro   -> cercania al centro educativo del alumno
         precio   -> between sobre el precio de la modalidad pedida
         modalidad-> presencial, online o ambas
         puntaje  -> puntaje_promedio >= puntaje_min
      3. Si vinieron dia o franja, pasar los ids candidatos por
         agenda.logica.filtrar_con_hueco(). Se hace al final, sobre la lista ya
         recortada, no sobre todos los profesores de la base.
      4. Ordenar por distancia, puntaje o precio; paginar de a 20.
      5. Devolver {"total", "pagina", "por_pagina", "resultados"}.
    """
    raise NotImplementedError("P2 - busqueda: la busqueda con los nueve filtros")


def pines_mapa(db: Session, filtros=None, ids: list[int] | None = None) -> list[dict]:
    """Coordenadas para Leaflet. Sirve a tres pantallas con el mismo codigo.

      1a: el mapa de cercanos, filtrado por barrio
      1c: los resultados de la busqueda actual
      1f: el mini mapa de la ficha, con un solo id

    Por eso acepta o filtros o una lista de ids.

    TODO (P2): implementar. Devolver solo profesores con lat y lon cargadas:
    uno sin coordenadas no se puede dibujar y no tiene que aparecer.
    """
    raise NotImplementedError("P2 - busqueda: pines para Leaflet")


def cercanos(db: Session, barrio_id=None, centro_id=None, con_hueco=False, limite=5) -> list[dict]:
    """El carrusel "Profes cerca de ti" de 1a.

    Ordena por distancia al barrio del alumno o a su centro educativo. Si
    con_hueco es True, ademas trae la primera hora libre de cada uno.

    TODO (P2): implementar.
      1. Resolver el punto de referencia con catalogos.logica.centroide_barrio()
         o las coordenadas del centro educativo.
      2. Calcular la distancia. Sin PostGIS: alcanza con la formula del
         haversine en SQL, o incluso ordenar por la diferencia de coordenadas
         al cuadrado, que para Montevideo da el mismo orden.
      3. Si con_hueco, pedirle a agenda la primera hora libre de cada uno.
    """
    raise NotImplementedError("P2 - busqueda: carrusel de cercanos")


def mejor_puntuados(db: Session, etapa_id=None, limite=3) -> list[dict]:
    """Los mejor rankeados del momento, para el podio de 1a.

    TODO (P2): implementar.
      1. Filtrar por ficha publicada y, si viene, por etapa.
      2. Exigir un minimo de resenas (por ejemplo 5) o un profesor con una
         sola resena de 5 estrellas le gana a uno con cincuenta de 4,8.
      3. Ordenar por puntaje_promedio desc y cortar en `limite`.
    """
    raise NotImplementedError("P2 - busqueda: ranking de mejor puntuados")
