"""Funciones publicas del modulo perfiles - dueno P1.

perfiles sirve la ficha publica. Es el modulo que mas consultan los demas.

Quien consume que:
  - cuentas  -> crear_perfil_estudiante(), crear_perfil_profesor() en el registro
  - cuentas  -> cabecera_estudiante() para GET /usuarios/yo
  - busqueda -> candidatos_publicados() y ficha_resumida() para armar resultados
  - agenda   -> reglas_profesor() para calcular los huecos libres
  - clases   -> precio_vigente() para cotizar
  - resenas  -> escribir_puntaje() al recalcular el promedio
"""

from decimal import Decimal

from sqlalchemy.orm import Session


# --- Alta, la llama cuentas en el registro ----------------------------------

def crear_perfil_estudiante(db: Session, usuario_id: int) -> object:
    """Crea un perfil_estudiante vacio para un usuario recien registrado.

    Vacio a proposito: el alumno completa etapa, centro y direccion despues,
    desde 1e. Sin esta fila, GET /usuarios/yo no tiene de donde sacar la
    cabecera de 1a.

    TODO (P1): implementar. db.add + db.flush, sin commit.
    """
    raise NotImplementedError("P1 - perfiles: crear el perfil del estudiante")


def crear_perfil_profesor(db: Session, usuario_id: int) -> object:
    """Crea un perfil_profesor en estado borrador.

    Borrador quiere decir que NO aparece en la busqueda. Se publica desde 1j
    cuando el profesor completo materias, precios y disponibilidad.

    TODO (P1): implementar. db.add + db.flush, sin commit.
    """
    raise NotImplementedError("P1 - perfiles: crear el perfil del profesor")


# --- Lectura, la llaman los otros modulos -----------------------------------

def cabecera_estudiante(db: Session, usuario_id: int) -> dict | None:
    """Etapa, nivel, centro, barrio y puntaje del alumno, con los nombres ya resueltos.

    Es el bloque "estudiante" de GET /usuarios/yo, o sea el subtitulo de 1a:
    "5.o de Bachillerato - Liceo Bauza - Cordon".

    Devuelve None si el usuario no es estudiante.

    TODO (P1): implementar. Hace falta un join con los catalogos para traer los
    nombres, no los ids: la cabecera muestra texto.
    """
    raise NotImplementedError("P1 - perfiles: datos de cabecera del estudiante")


def perfil_profesor_de(db: Session, usuario_id: int) -> object | None:
    """Devuelve el PerfilProfesor de un usuario, o None.

    OJO con los dos ids: usuario.id no es perfil_profesor.id. Casi todas las
    tablas de la oferta y de la agenda cuelgan del perfil, no del usuario; las
    clases y los hilos cuelgan del usuario. Esta funcion es el puente.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 - perfiles: perfil del profesor por usuario_id")


def reglas_profesor(db: Session, perfil_profesor_id: int) -> dict:
    """Las reglas con las que agenda calcula los huecos libres.

    Devuelve duracion_min, duracion_max, duraciones ofrecidas, descanso_min,
    max_clases_dia y aviso_minimo_horas.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 - perfiles: reglas de duracion y agenda")


def precio_vigente(db: Session, usuario_profesor_id: int, modalidad: str) -> Decimal | None:
    """El precio por hora actual del profesor para esa modalidad.

    Lo llama clases al cotizar. Es el precio de HOY: la clase lo congela al
    crearse, y de ahi en mas no cambia aunque el profesor lo suba.

    TODO (P1): implementar. presencial -> precio_hora_presencial,
    online -> precio_hora_online.
    """
    raise NotImplementedError("P1 - perfiles: precio vigente del profesor")


def ficha_resumida(db: Session, ids_usuario: list[int]) -> list[dict]:
    """Version liviana de varios profesores, en UNA consulta.

    Es lo que devuelve GET /profesores/resumen?ids=1,2,3, y lo que usa busqueda
    para armar las filas de resultados sin pedir la ficha completa de cada uno.

    TODO (P1): implementar. Cuidado con el N+1: una sola consulta con join a
    profesor_materia, no un SELECT por profesor.
    """
    raise NotImplementedError("P1 - perfiles: resumen de profesores en lote")


def escribir_puntaje(db: Session, usuario_id: int, promedio: Decimal, cantidad: int) -> None:
    """Guarda el puntaje desnormalizado en el perfil que corresponda.

    Es la UNICA puerta por la que se escriben puntaje_promedio y
    cantidad_resenas, y solo la llama el modulo resenas. Si alguien mas los
    escribe, los numeros dejan de coincidir con la tabla de resenas.

    Sirve para los dos perfiles: mira el rol del usuario y actualiza el correcto.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 - perfiles: escribir el puntaje desnormalizado")
