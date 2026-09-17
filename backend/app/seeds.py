"""Datos de prueba. Se corre con:  python -m app.seeds

Va APARTE de las migraciones a proposito: las migraciones cambian la forma de
las tablas, los datos de ejemplo se pueden volver a cargar cuantas veces haga
falta. Si estuvieran mezclados, resetear los datos obligaria a bajar y volver
a subir el esquema.

Tiene que ser IDEMPOTENTE: correrlo dos veces no puede duplicar nada. La forma
mas simple es borrar y volver a cargar, en el orden inverso al de las FK.

QUE CARGA (segun la spec):
  - los barrios de Montevideo con su centroide
  - las materias del mockup
  - las etapas educativas
  - unos cuantos centros educativos
  - los idiomas
  - la comision de servicio y la tasa de IVA
  - unos veinte usuarios de ejemplo, con sus perfiles, disponibilidad y clases
"""

from app.db import SesionLocal

# ---------------------------------------------------------------------------
# Listas de referencia. Estas son datos reales y se pueden usar tal cual.
# ---------------------------------------------------------------------------

BARRIOS = [
    # (nombre, latitud, longitud) - centroide aproximado
    ("Cordon", -34.9011, -56.1780),
    ("Centro", -34.9059, -56.1913),
    ("Pocitos", -34.9139, -56.1560),
    ("Punta Carretas", -34.9260, -56.1600),
    ("Parque Rodo", -34.9160, -56.1700),
    ("Tres Cruces", -34.8940, -56.1660),
    ("La Blanqueada", -34.8850, -56.1560),
    ("Buceo", -34.9020, -56.1370),
    ("Malvin", -34.8930, -56.1180),
    ("Ciudad Vieja", -34.9070, -56.2050),
    ("Prado", -34.8580, -56.1950),
    ("Union", -34.8730, -56.1250),
]

MATERIAS = [
    ("Matematica", "Mate"),
    ("Fisica", "Fisica"),
    ("Quimica", "Quimica"),
    ("Idioma Espanol", "Espanol"),
    ("Ingles", "Ingles"),
    ("Historia", "Historia"),
    ("Biologia", "Biologia"),
    ("Literatura", "Literatura"),
    ("Geografia", "Geografia"),
    ("Dibujo", "Dibujo"),
]

# ============================== IMPORTANTE ==============================
# Esta lista es LA QUE MANDA. El esquema viejo del equipo decia escuela,
# liceo, orientacion y facultad; el mockup filtra por estas cinco. Todo el
# filtrado de 1c depende de que sea una sola lista.
# Es una de las dos cosas que la spec marca como "decidir antes de la semana 2".
# =======================================================================
ETAPAS = [
    ("Ciclo basico", 1, ["1.o", "2.o", "3.o"]),
    ("Bachillerato", 2, ["4.o", "5.o", "6.o"]),
    ("UTU", 3, ["1.o", "2.o", "3.o"]),
    ("Universidad", 4, ["1.o", "2.o", "3.o", "4.o", "5.o"]),
    ("Examen de ingreso", 5, []),
]

CENTROS = [
    # (nombre, tipo, barrio)
    ("Liceo Bauza", "liceo", "Cordon"),
    ("Liceo N 8", "liceo", "Pocitos"),
    ("IAVA", "liceo", "Centro"),
    ("UTU Buceo", "utu", "Buceo"),
    ("Liceo 14", "liceo", "La Blanqueada"),
    ("Facultad de Ingenieria", "facultad", "Parque Rodo"),
]

IDIOMAS = ["Espanol", "Ingles", "Portugues"]

# Comision de la plataforma e IVA. En tabla y no como constante para poder
# cambiarlos sin recompilar. El IVA uruguayo basico es 22 %.
PARAMETROS = [
    ("comision_servicio", 10.0),
    ("tasa_iva", 22.0),
]


def limpiar(db) -> None:
    """Borra todo, en el orden inverso al de las claves foraneas.

    TODO (semana 1): implementar.
    Orden sugerido: cobro, tarjeta, mensaje, hilo, resena, clase, bloqueo,
    franja_disponibilidad, las siete de la oferta del profesor, los dos
    perfiles, usuario, y al final los catalogos.
    """
    raise NotImplementedError("Semana 1: limpiar la base antes de sembrar")


def sembrar_catalogos(db) -> dict:
    """Carga barrios, materias, etapas, centros, idiomas y parametros.

    Devuelve un diccionario con los ids creados, para que las funciones
    siguientes puedan referenciarlos sin volver a consultar.

    TODO (semana 1): implementar. Los centros necesitan el id del barrio, asi
    que van despues de los barrios.
    """
    raise NotImplementedError("Semana 1: sembrar los catalogos")


def sembrar_usuarios(db, catalogos: dict) -> dict:
    """Crea unos veinte usuarios de ejemplo: alumnos y profesores.

    Todos con la misma contrasena, para poder entrar con cualquiera mientras
    se prueba. Sugerencia: correo tipo profe1@exonero.test y clave "exonero123".

    TODO (semana 1): implementar.
      1. Hashear la clave UNA sola vez y reusar el hash: bcrypt es lento a
         proposito, y veinte hashes hacen que el seed tarde varios segundos.
      2. Por cada profesor, crear su perfil con materias, precios, barrio y
         coordenadas dentro de Montevideo.
      3. Publicar la ficha de la mayoria (estado_ficha = publicada) o la
         busqueda de 1c va a aparecer vacia.
    """
    raise NotImplementedError("Semana 1: sembrar usuarios y perfiles")


def sembrar_agenda(db, usuarios: dict) -> None:
    """Carga franjas de disponibilidad para cada profesor.

    TODO (semana 1): implementar. Sin franjas, el calendario de 1f sale vacio
    y no se puede reservar nada: es lo primero que se nota al probar.
    """
    raise NotImplementedError("Semana 1: sembrar la disponibilidad")


def sembrar_clases(db, usuarios: dict) -> None:
    """Crea clases de ejemplo en los distintos estados.

    Hacen falta de los cuatro tipos para que las pantallas se vean llenas:
      - pendientes  para que 1i tenga solicitudes que aprobar
      - aprobadas   para que 1a y 1b tengan proxima clase
      - dictadas    para el historial de 1b y las metricas de 1d
      - canceladas  para la tasa de cancelacion de 1d

    TODO (semana 1): implementar. Cada clase necesita su cobro asociado, con
    el estado que corresponda al de la clase.
    """
    raise NotImplementedError("Semana 1: sembrar clases y cobros")


def main() -> None:
    """Corre todo el sembrado en una sola transaccion."""
    db = SesionLocal()
    try:
        limpiar(db)
        catalogos = sembrar_catalogos(db)
        usuarios = sembrar_usuarios(db, catalogos)
        sembrar_agenda(db, usuarios)
        sembrar_clases(db, usuarios)
        db.commit()
        print("Datos de prueba cargados.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
