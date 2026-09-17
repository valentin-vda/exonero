"""Funciones publicas del modulo resenas - dueno P3.

resenas es el UNICO modulo que escribe puntaje_promedio y cantidad_resenas en
los perfiles. Si alguien mas los toca, los numeros dejan de coincidir con la
tabla de resenas y no hay forma de saber cual esta bien.

A quien le pide datos:
  - clases   -> tuvieron_clase(), para exigir que solo resene quien tuvo clase
  - perfiles -> escribir_puntaje(), para guardar el promedio recalculado
"""

from sqlalchemy.orm import Session


def dejar_o_editar(db: Session, autor_id: int, autor_rol: str, datos) -> object:
    """Crea la resena, o actualiza la que esa persona ya habia dejado.

    El sentido sale del rol del token, no del cuerpo: si el autor es
    estudiante, es alumno_a_profesor; si es profesor, profesor_a_alumno.

    TODO (P3): implementar.
      1. 403 "sin_clases_con_esa_persona" si
         clases.logica.tuvieron_clase(db, autor_id, destinatario_id) es False.
      2. Buscar si ya existe (autor_id, destinatario_id).
         - En POST, si existe -> 409 "ya_resenado" (que use PUT).
         - En PUT, si no existe -> 404.
      3. Guardar puntaje y texto.
      4. recalcular(db, destinatario_id). SIEMPRE, si no el promedio queda viejo.
    """
    raise NotImplementedError("P3 - resenas: dejar o editar la resena")


def recalcular(db: Session, usuario_id: int) -> None:
    """Recalcula el promedio y la cantidad, y los escribe en el perfil.

    Se llama despues de cada alta o edicion. Es la unica forma en que
    puntaje_promedio y cantidad_resenas cambian de valor.

    TODO (P3): implementar.
      1. SELECT avg(puntaje), count(*) FROM resena WHERE destinatario_id = ...
      2. perfiles.logica.escribir_puntaje(db, usuario_id, promedio, cantidad).
         perfiles se fija solo si el perfil es de estudiante o de profesor.
    """
    raise NotImplementedError("P3 - resenas: recalcular el puntaje")


def resumen(db: Session, usuario_id: int) -> dict:
    """Promedio, cantidad y distribucion por estrella.

    Sirve igual para un profesor y para un alumno.

    TODO (P3): implementar. La distribucion se saca con un
    GROUP BY puntaje, y hay que completar con cero las estrellas que no
    aparecieron: el grafico de 1f necesita las cinco barras siempre.
    """
    raise NotImplementedError("P3 - resenas: resumen y distribucion")


def resena_de(db: Session, autor_id: int, destinatario_id: int) -> dict | None:
    """La resena que una persona le dejo a otra, o None.

    Es el campo mi_resena de GET /clases/mis-profesores y /mis-alumnos. Aca SI
    se devuelve, porque es la propia: el autor puede ver y editar la suya.

    TODO (P3): implementar.
    """
    raise NotImplementedError("P3 - resenas: la resena propia hacia otra persona")
