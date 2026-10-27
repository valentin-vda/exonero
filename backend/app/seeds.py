"""Datos de prueba. Se corre con:  python -m app.seeds

Va APARTE de las migraciones a proposito: las migraciones cambian la forma de
las tablas, los datos de ejemplo se pueden volver a cargar cuantas veces haga
falta. Si estuvieran mezclados, resetear los datos obligaria a bajar y volver
a subir el esquema.

Tiene que ser IDEMPOTENTE: correrlo dos veces no puede duplicar nada. Por eso
arranca vaciando todas las tablas (ver limpiar) y vuelve a cargar todo. Y es
DETERMINISTA: todo lo "al azar" sale de random.Random con una semilla fija, asi
que en todas las maquinas quedan los mismos datos. Lo unico que cambia son las
fechas, que se calculan desde HOY: siempre hay clases pasadas y proximas sin
importar cuando se corra.

QUE CARGA (las 24 tablas):
  - catalogos: 26 barrios de Montevideo con su centroide, 16 materias, las
    cinco etapas, 22 centros educativos, 5 idiomas, y la comision y el IVA con
    su historia
  - 34 profesores (29 con la ficha publicada, 3 en borrador y 2 pausadas) con
    toda su oferta: materias, etapas, idiomas, zonas, duraciones, como es una
    clase con ellos y algunas fotos del lugar
  - 60 alumnos con su perfil y entre una y tres tarjetas de prueba (algunas
    vencidas o dadas de baja)
  - la agenda: las franjas semanales de todos y bloqueos puntuales de algunos
  - mas de mil clases: cinco meses de historia (dictadas, canceladas, no
    asistidas) y las proximas dos semanas (aprobadas, pendientes, alguna
    cancelada), cada una con su cobro; y solicitudes rechazadas, que dejan un
    cobro liberado sin clase
  - resenas en los dos sentidos, solo entre quienes tuvieron clase dictada,
    con el puntaje promedio ya escrito en cada perfil
  - conversaciones de mensajeria, algunas con mensajes sin leer

Al terminar imprime cuanto quedo en cada tabla.

Todos los usuarios entran con la clave "exonero123":
  profe1@example.com ... profe34@example.com
  alumno1@example.com ... alumno60@example.com

LOS VEINTE DE SIEMPRE NO CAMBIAN. profe1..profe8 y alumno1..alumno12 tienen
los mismos datos y los mismos ids que antes de que los seeds crecieran: se
crean primero, y los nuevos van despues. Cuentan con eso los botones de
"Usuarios de prueba" del login y backend/verificar_p4.py (por ejemplo, que
alumno1 tenga una sola tarjeta, que profe7 este en borrador y profe8 pausada).
Lo que si cambio son sus clases: ahora tienen historia.

Por que example.com: es un dominio reservado para ejemplos (RFC 2606), no es
de nadie. Un dominio .test seria lo mas natural, pero el validador de correos
del backend (EmailStr) lo rechaza por ser de "uso especial", y con esos
usuarios no se podria hacer login.
"""

import base64
import random
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.config import ajustes
from app.db import SesionLocal
from app.enums import (
    Actor,
    EstadoClase,
    EstadoCobro,
    EstadoFicha,
    Formato,
    LugarClase,
    Modalidad,
    Rol,
    SentidoResena,
    TipoCentro,
)
from app.registro_modelos import metadata
from app.seguridad import hashear_clave

# seeds no es un modulo: es el unico script que escribe en las tablas de los
# nueve a la vez, asi que importa los modelos de todos.
from app.modulos.agenda.modelos import Bloqueo, FranjaDisponibilidad
from app.modulos.catalogos.modelos import (
    Barrio,
    CentroEducativo,
    EtapaEducativa,
    Idioma,
    Materia,
    ParametroPlataforma,
)
from app.modulos.clases.logica import desglosar, importes_congelados
from app.modulos.clases.modelos import Clase
from app.modulos.cuentas.modelos import Usuario
from app.modulos.mensajeria.modelos import Hilo, Mensaje
from app.modulos.pagos.modelos import Cobro, Tarjeta
from app.modulos.perfiles.modelos import (
    FotoLugar,
    PerfilEstudiante,
    PerfilProfesor,
    ProfesorDuracion,
    ProfesorEtapa,
    ProfesorIdioma,
    ProfesorMateria,
    ProfesorZona,
    PuntoMetodo,
)
from app.modulos.resenas import logica as resenas
from app.modulos.resenas.modelos import Resena

CLAVE_DE_PRUEBA = "exonero123"
ZONA = ZoneInfo(ajustes.ZONA_HORARIA)
FOTO_AULA = Path(__file__).with_name("datos") / "aula-ejemplo.jpg"

# Semilla fija: lo "al azar" sale igual en todas las maquinas.
SEMILLA = 2026

# Cuanta historia y cuanto futuro tienen las clases.
SEMANAS_DE_HISTORIA = 20
# Dos semanas y no mas: verificar_p4.py reserva sus clases de prueba a partir
# del dia 15, y con clases sembradas ahi se pisarian.
DIAS_POR_DELANTE = 14

# Topes de clases. GET /clases pagina de a 50, y verificar_p4.py compara la
# primera pagina de alumno1 y de profe1 con la base: si alguno pasara de 50
# (contando las que crea el propio script), esa comprobacion fallaria.
MAX_CLASES_PROFESOR = 38
MAX_CLASES_ALUMNO = 28

# ---------------------------------------------------------------------------
# Catalogos. Estos son datos reales y se pueden usar tal cual.
# Los doce primeros barrios, las diez primeras materias, los seis primeros
# centros y los tres primeros idiomas son los de siempre: van primero para
# conservar sus ids.
# ---------------------------------------------------------------------------

BARRIOS = [
    # (nombre, latitud, longitud) - centroide aproximado
    ("Cordón", -34.9011, -56.1780),
    ("Centro", -34.9059, -56.1913),
    ("Pocitos", -34.9139, -56.1560),
    ("Punta Carretas", -34.9260, -56.1600),
    ("Parque Rodó", -34.9160, -56.1700),
    ("Tres Cruces", -34.8940, -56.1660),
    ("La Blanqueada", -34.8850, -56.1560),
    ("Buceo", -34.9020, -56.1370),
    ("Malvín", -34.8930, -56.1180),
    ("Ciudad Vieja", -34.9070, -56.2050),
    ("Prado", -34.8580, -56.1950),
    ("Unión", -34.8730, -56.1250),
    ("Carrasco", -34.8870, -56.0560),
    ("Punta Gorda", -34.8960, -56.0830),
    ("Malvín Norte", -34.8800, -56.1040),
    ("Palermo", -34.9110, -56.1830),
    ("Barrio Sur", -34.9100, -56.1960),
    ("Aguada", -34.8920, -56.1900),
    ("La Comercial", -34.8900, -56.1720),
    ("Jacinto Vera", -34.8780, -56.1720),
    ("Brazo Oriental", -34.8650, -56.1700),
    ("Atahualpa", -34.8640, -56.1880),
    ("Paso Molino", -34.8590, -56.2080),
    ("Belvedere", -34.8510, -56.2170),
    ("Sayago", -34.8350, -56.2100),
    ("Peñarol", -34.8240, -56.2000),
]

MATERIAS = [
    ("Matemática", "Mate"),
    ("Física", "Física"),
    ("Química", "Química"),
    ("Idioma Español", "Español"),
    ("Inglés", "Inglés"),
    ("Historia", "Historia"),
    ("Biología", "Biología"),
    ("Literatura", "Literatura"),
    ("Geografía", "Geografía"),
    ("Dibujo", "Dibujo"),
    ("Filosofía", "Filosofía"),
    ("Economía", "Economía"),
    ("Contabilidad", "Contabilidad"),
    ("Programación", "Programación"),
    ("Francés", "Francés"),
    ("Portugués", "Portugués"),
]

# ============================== IMPORTANTE ==============================
# Esta lista es LA QUE MANDA. El esquema viejo del equipo decia escuela,
# liceo, orientacion y facultad; el mockup filtra por estas cinco. Todo el
# filtrado de 1c depende de que sea una sola lista.
# Es una de las dos cosas que la spec marca como "decidir antes de la semana 2".
# =======================================================================
ETAPAS = [
    ("Ciclo básico", 1, ["1.o", "2.o", "3.o"]),
    ("Bachillerato", 2, ["4.o", "5.o", "6.o"]),
    ("UTU", 3, ["1.o", "2.o", "3.o"]),
    ("Universidad", 4, ["1.o", "2.o", "3.o", "4.o", "5.o"]),
    ("Examen de ingreso", 5, []),
]

CENTROS = [
    # (nombre, tipo, barrio)
    ("Liceo Bauzá", "liceo", "Cordón"),
    ("Liceo N 8", "liceo", "Pocitos"),
    ("IAVA", "liceo", "Centro"),
    ("UTU Buceo", "utu", "Buceo"),
    ("Liceo 14", "liceo", "La Blanqueada"),
    ("Facultad de Ingeniería", "facultad", "Parque Rodó"),
    ("Liceo Zorrilla", "liceo", "Punta Carretas"),
    ("Liceo Miranda", "liceo", "Barrio Sur"),
    ("Liceo Rodó", "liceo", "Centro"),
    ("Colegio Elbio Fernández", "liceo", "Centro"),
    ("Liceo Larrañaga", "liceo", "Jacinto Vera"),
    ("Liceo Carrasco", "liceo", "Carrasco"),
    ("Liceo 10 Malvín", "liceo", "Malvín"),
    ("Liceo 26 Sayago", "liceo", "Sayago"),
    ("UTU Arroyo Seco", "utu", "Aguada"),
    ("UTU Malvín Norte", "utu", "Malvín Norte"),
    ("Facultad de Ciencias Económicas", "facultad", "Cordón"),
    ("Facultad de Química", "facultad", "La Comercial"),
    ("Facultad de Medicina", "facultad", "La Comercial"),
    ("Universidad ORT", "facultad", "Pocitos"),
    ("Universidad Católica", "facultad", "La Blanqueada"),
    ("Instituto de Profesores Artigas", "instituto", "Aguada"),
]

IDIOMAS = ["Español", "Inglés", "Portugués", "Francés", "Italiano"]

# Comision de la plataforma e IVA, con su historia: la tabla guarda desde
# cuando vale cada valor, y parametros_vigentes() toma el ultimo que ya
# empezo. El IVA uruguayo basico es 22 %.
PARAMETROS = [
    # (clave, valor, vigente desde)
    ("comision_servicio", 8.0, date(2024, 1, 1)),
    ("tasa_iva", 22.0, date(2024, 1, 1)),
    ("comision_servicio", 10.0, date(2025, 1, 1)),
]

# ---------------------------------------------------------------------------
# Profesores. Personas inventadas.
# Los ocho primeros son los de siempre (ver el docstring del modulo).
# ---------------------------------------------------------------------------


def _profe(nombre, apellido, barrio, modalidad, lugar, materias, etapas, precios, titulo, anios,
           titular, horario, direccion=None, idiomas=("Español",), ficha=EstadoFicha.publicada,
           **reglas) -> dict:
    """Un profesor de la segunda tanda, en pocas lineas.

    precios es (presencial, online); None si no da esa modalidad. horario es
    una clave de HORARIOS. reglas son las de la seccion "Reglas" de 1j
    (descanso_min, max_clases_dia, aviso_minimo_horas, formato, cupo_min,
    cupo_max, duracion_max).
    """
    presencial, online = precios
    return dict(
        nombre=nombre, apellido=apellido, barrio=barrio, direccion=direccion,
        modalidad=modalidad, lugar=lugar, materias=list(materias), etapas=list(etapas),
        idiomas=list(idiomas), precio_presencial=presencial, precio_online=online,
        titular=titular, titulo=titulo, anios=anios, ficha=ficha, horario=horario, reglas=reglas,
    )


PRESENCIAL, ONLINE, AMBAS = Modalidad.presencial, Modalidad.online, Modalidad.ambas
ESPACIO, DOMICILIO, AMBOS, PUBLICO = (
    LugarClase.espacio_propio, LugarClase.a_domicilio, LugarClase.ambos, LugarClase.espacio_publico,
)
CB, BACH, UTU, UNI, EXAMEN = "Ciclo básico", "Bachillerato", "UTU", "Universidad", "Examen de ingreso"

PROFESORES = [
    dict(
        nombre="Lucia", apellido="Fernandez", barrio="Pocitos", direccion="Benito Blanco 1120",
        modalidad=Modalidad.ambas, lugar=LugarClase.espacio_propio,
        materias=["Matemática", "Física"], etapas=["Bachillerato", "Examen de ingreso"],
        idiomas=["Español"], precio_presencial=900, precio_online=800,
        titular="Matematica y Fisica para bachillerato y examenes de ingreso",
        titulo="Profesora de Matematica (IPA)", anios=8, ficha=EstadoFicha.publicada,
    ),
    dict(
        nombre="Martin", apellido="Rodriguez", barrio="Cordón", direccion=None,
        modalidad=Modalidad.presencial, lugar=LugarClase.a_domicilio,
        materias=["Química", "Biología"], etapas=["Ciclo básico", "Bachillerato"],
        idiomas=["Español"], precio_presencial=850, precio_online=None,
        titular="Quimica sin miedo, a domicilio",
        titulo="Quimico Farmaceutico (Udelar)", anios=5, ficha=EstadoFicha.publicada,
        duracion_max=90,
    ),
    dict(
        nombre="Sofia", apellido="Pereira", barrio="Centro", direccion=None,
        modalidad=Modalidad.online, lugar=LugarClase.espacio_propio,
        materias=["Inglés"], etapas=["Ciclo básico", "Bachillerato", "Universidad"],
        idiomas=["Español", "Inglés"], precio_presencial=None, precio_online=700,
        titular="Ingles conversacional y preparacion de examenes internacionales",
        titulo="Profesora de Ingles (IPA)", anios=10, ficha=EstadoFicha.publicada,
    ),
    dict(
        nombre="Diego", apellido="Silva", barrio="Parque Rodó", direccion="Jackson 1045",
        modalidad=Modalidad.ambas, lugar=LugarClase.ambos,
        materias=["Matemática"], etapas=["Universidad", "UTU"],
        idiomas=["Español", "Inglés", "Portugués"], precio_presencial=1100, precio_online=1000,
        titular="Calculo y Algebra para facultad",
        titulo="Ingeniero en Computacion (Udelar)", anios=6, ficha=EstadoFicha.publicada,
    ),
    dict(
        nombre="Valentina", apellido="Gomez", barrio="Buceo", direccion="Rivera 4410",
        modalidad=Modalidad.presencial, lugar=LugarClase.espacio_propio,
        materias=["Literatura", "Idioma Español", "Historia"], etapas=["Ciclo básico", "Bachillerato"],
        idiomas=["Español"], precio_presencial=750, precio_online=None,
        titular="Literatura, Espanol e Historia para liceo",
        titulo="Profesora de Literatura (IPA)", anios=12, ficha=EstadoFicha.publicada,
    ),
    dict(
        nombre="Joaquin", apellido="Sosa", barrio="Tres Cruces", direccion=None,
        modalidad=Modalidad.ambas, lugar=LugarClase.a_domicilio,
        materias=["Física", "Matemática"], etapas=["Bachillerato", "Examen de ingreso"],
        idiomas=["Español"], precio_presencial=950, precio_online=850,
        titular="Fisica y Matematica para salvar el examen",
        titulo="Estudiante avanzado de Ingenieria", anios=3, ficha=EstadoFicha.publicada,
        duracion_max=90,
    ),
    dict(
        nombre="Camila", apellido="Martinez", barrio="Malvín", direccion=None,
        modalidad=Modalidad.online, lugar=LugarClase.espacio_propio,
        materias=["Geografía", "Historia"], etapas=["Ciclo básico"],
        idiomas=["Español"], precio_presencial=None, precio_online=650,
        titular="Geografia e Historia para ciclo basico",
        titulo="Estudiante de profesorado de Historia", anios=2, ficha=EstadoFicha.borrador,
    ),
    dict(
        nombre="Nicolas", apellido="Acosta", barrio="Prado", direccion="Plaza Fabini",
        modalidad=Modalidad.presencial, lugar=LugarClase.espacio_publico,
        materias=["Dibujo"], etapas=["Bachillerato", "UTU"],
        idiomas=["Español"], precio_presencial=800, precio_online=None,
        titular="Dibujo tecnico y geometria descriptiva",
        titulo="Arquitecto (Udelar)", anios=7, ficha=EstadoFicha.pausada,
    ),
    # --- La segunda tanda: profe9 a profe34 ---
    _profe("Florencia", "Bentancor", "Punta Carretas", AMBAS, ESPACIO, ["Inglés"], [CB, BACH, EXAMEN],
           (850, 750), "Profesora de Inglés (IPA) y Cambridge CAE", 9,
           "Inglés para liceo y exámenes Cambridge", "manana", direccion="Ellauri 520",
           idiomas=["Español", "Inglés"]),
    _profe("Gonzalo", "Pintos", "Centro", ONLINE, ESPACIO, ["Programación", "Matemática"], [UTU, UNI],
           (None, 950), "Analista en Sistemas (ORT)", 6,
           "Programación desde cero: Python, Java y algoritmos", "noche"),
    _profe("Mariana", "Cardozo", "Pocitos", PRESENCIAL, DOMICILIO, ["Química", "Biología"], [BACH, EXAMEN],
           (900, None), "Química Farmacéutica (Udelar)", 7,
           "Química y Biología para el ingreso a Medicina", "tarde", descanso_min=15, duracion_max=90),
    _profe("Sebastián", "Correa", "Unión", AMBAS, AMBOS, ["Matemática", "Física"], [CB, BACH],
           (800, 700), "Profesor de Matemática (IPA)", 15,
           "Matemática paso a paso para liceo", "tarde", direccion="8 de Octubre 3240",
           max_clases_dia=5),
    _profe("Agustina", "Rivero", "Malvín", PRESENCIAL, ESPACIO, ["Literatura", "Filosofía"], [BACH],
           (780, None), "Profesora de Filosofía (IPA)", 11,
           "Filosofía y Literatura: pensar y escribir mejor", "mixto", direccion="Michigan 1540"),
    _profe("Federico", "Larrosa", "Tres Cruces", ONLINE, ESPACIO, ["Contabilidad", "Economía"], [UTU, UNI],
           (None, 900), "Contador Público (Udelar)", 8,
           "Contabilidad y Economía para facultad", "noche", aviso_minimo_horas=24),
    _profe("Valeria", "Techera", "Buceo", AMBAS, ESPACIO, ["Francés"], [CB, BACH, UNI],
           (850, 750), "Profesora de Francés (Alianza Francesa)", 10,
           "Francés para todas las edades", "manana", direccion="Av. Rivera 3980",
           idiomas=["Español", "Francés"]),
    _profe("Rodrigo", "Bianchi", "Ciudad Vieja", PRESENCIAL, PUBLICO, ["Historia", "Geografía"], [CB, BACH],
           (700, None), "Profesor de Historia (IPA)", 6,
           "Historia y Geografía con mapas y casos reales", "tarde", direccion="Biblioteca Nacional"),
    _profe("Natalia", "Sena", "Prado", AMBAS, DOMICILIO, ["Matemática"], [CB, UTU],
           (750, 680), "Maestra y estudiante de profesorado de Matemática", 4,
           "Matemática para ciclo básico y UTU, con paciencia", "tarde", descanso_min=30),
    _profe("Pablo", "Ferreira", "Parque Rodó", AMBAS, AMBOS, ["Física"], [BACH, UNI, EXAMEN],
           (1050, 950), "Licenciado en Física (Udelar)", 9,
           "Física I y II: mecánica y electromagnetismo", "noche", direccion="Gonzalo Ramírez 1650",
           aviso_minimo_horas=24),
    _profe("Carolina", "Méndez", "Cordón", ONLINE, ESPACIO, ["Idioma Español", "Literatura"], [CB, BACH, EXAMEN],
           (None, 650), "Correctora y profesora de Idioma Español", 13,
           "Ortografía, redacción y comprensión lectora", "mixto"),
    _profe("Ignacio", "Olivera", "Pocitos", PRESENCIAL, ESPACIO, ["Dibujo"], [BACH, UTU, EXAMEN],
           (850, None), "Arquitecto (Udelar)", 8,
           "Dibujo técnico e ingreso a Arquitectura", "manana", direccion="21 de Setiembre 2890"),
    _profe("Daniela", "Ruiz", "La Blanqueada", AMBAS, AMBOS, ["Biología"], [CB, BACH, EXAMEN],
           (820, 720), "Licenciada en Biología (Udelar)", 6,
           "Biología clara, con esquemas y mucho repaso", "tarde", direccion="Av. Larrañaga 3410"),
    _profe("Matías", "Castillo", "Centro", ONLINE, ESPACIO, ["Portugués", "Inglés"], [CB, BACH, UNI],
           (None, 700), "Traductor Público (Udelar)", 7,
           "Portugués e Inglés conversacional", "noche", idiomas=["Español", "Portugués", "Inglés"]),
    _profe("Andrea", "Silveira", "Punta Carretas", PRESENCIAL, ESPACIO, ["Matemática", "Contabilidad"], [UTU, UNI],
           (950, None), "Contadora y profesora de Matemática Financiera", 12,
           "Matemática financiera y Contabilidad", "tarde", direccion="José Ellauri 1120"),
    _profe("Tomás", "Viera", "Tres Cruces", AMBAS, DOMICILIO, ["Química"], [CB, BACH],
           (780, 700), "Estudiante avanzado de Química (Udelar)", 3,
           "Química sin vueltas para liceo", "tarde", descanso_min=30, max_clases_dia=3),
    _profe("Lorena", "Paz", "Unión", ONLINE, ESPACIO, ["Historia", "Filosofía"], [BACH, EXAMEN],
           (None, 680), "Profesora de Historia (IPA)", 14,
           "Historia y Filosofía para bachillerato", "mixto",
           formato=Formato.ambos, cupo_min=2, cupo_max=4),
    _profe("Juan Pablo", "Ibarra", "Buceo", PRESENCIAL, ESPACIO, ["Física", "Matemática"], [UNI],
           (1150, None), "Ingeniero Eléctrico (Udelar)", 10,
           "Cálculo, Física y Circuitos para Ingeniería", "noche", direccion="Av. Italia 2970",
           max_clases_dia=4),
    _profe("Micaela", "Barrios", "Cordón", AMBAS, AMBOS, ["Inglés"], [CB, BACH],
           (800, 700), "Profesora de Inglés (IPA)", 5,
           "Inglés para liceo: gramática y conversación", "manana", direccion="Constituyente 1820",
           idiomas=["Español", "Inglés"]),
    _profe("Emiliano", "Rocha", "Prado", ONLINE, ESPACIO, ["Programación"], [UTU, UNI],
           (None, 850), "Estudiante de Ingeniería en Computación", 2,
           "Programación para principiantes", "noche", ficha=EstadoFicha.borrador),
    _profe("Gabriela", "Núñez", "Ciudad Vieja", PRESENCIAL, ESPACIO, ["Geografía"], [CB, BACH],
           (700, None), "Profesora de Geografía (IPA)", 18,
           "Geografía con salidas de campo", "manana", direccion="Sarandí 450",
           ficha=EstadoFicha.pausada),
    _profe("Hernán", "Acuña", "Parque Rodó", AMBAS, ESPACIO, ["Economía"], [BACH, UNI],
           (900, 800), "Economista (Udelar)", 4,
           "Economía para bachillerato y facultad", "tarde", direccion="Pablo de María 1100",
           ficha=EstadoFicha.borrador),
    _profe("Paula", "Cabrera", "Carrasco", AMBAS, ESPACIO, ["Matemática", "Física"], [CB, BACH, EXAMEN],
           (1000, 900), "Profesora de Matemática (IPA)", 16,
           "Matemática y Física en Carrasco, también online", "tarde", direccion="Av. Arocena 1580"),
    _profe("Bruno", "Ramos", "Sayago", PRESENCIAL, ESPACIO, ["Matemática", "Química"], [CB, UTU],
           (650, None), "Estudiante de profesorado de Química", 3,
           "Matemática y Química para ciclo básico y UTU", "tarde", direccion="Av. Millán 4350"),
    _profe("Verónica", "Alonso", "Palermo", ONLINE, ESPACIO, ["Biología", "Química"], [BACH, EXAMEN],
           (None, 800), "Doctora en Medicina (Udelar)", 9,
           "Biología y Química para el ingreso a Medicina", "noche"),
    _profe("Leandro", "Duarte", "Aguada", AMBAS, AMBOS, ["Inglés", "Portugués"], [CB, BACH, UTU],
           (750, 650), "Profesor de Inglés (IPA)", 7,
           "Inglés y Portugués para liceo y UTU", "mixto", direccion="Av. Agraciada 2160",
           idiomas=["Español", "Inglés", "Portugués"]),
]

# Las franjas semanales de cada estilo de profesor.
# dia_semana: 0 = domingo ... 6 = sabado, como Date.getDay() (ver agenda/modelos.py).
HORARIOS = {
    # Los ocho de siempre: unos de 14 a 20 con sabados de manana, otros de 15 a 21.
    "original_par": [(d, 14, 20) for d in range(1, 6)] + [(6, 9, 13)],
    "original_impar": [(d, 15, 21) for d in range(1, 6)],
    "tarde": [(d, 14, 20) for d in range(1, 6)],
    "manana": [(d, 8, 12) for d in range(1, 6)] + [(6, 9, 13)],
    "noche": [(d, 18, 22) for d in range(1, 5)],
    "mixto": [(1, 9, 12), (3, 9, 12), (5, 9, 12), (2, 15, 20), (4, 15, 20), (6, 10, 13)],
}

BIOGRAFIAS = [
    "Doy clases particulares hace {anios} años. {titulo}. Me gusta arrancar por lo que más te "
    "cuesta y avanzar a tu ritmo, con ejercicios parecidos a los de tus pruebas.",
    "{titulo}, con {anios} años dando clases. Preparo cada clase con el programa de tu curso y "
    "te dejo material para practicar entre una y otra.",
    "Hace {anios} años que acompaño a estudiantes de {etapas}. {titulo}. Explico con ejemplos de "
    "todos los días y sin apuro: la idea es que entiendas, no que memorices.",
    "{titulo}. Después de {anios} años de clases aprendí que cada alumno necesita algo distinto: "
    "la primera clase la usamos para ver dónde estás y armar un plan.",
]

# "Como es una clase conmigo" (1f y 1j). Los ocho de siempre usan solo METODO.
METODO = [
    "Arrancamos por lo que mas te cuesta, no por el orden del programa.",
    "En cada clase hacemos ejercicios de examenes anteriores.",
    "Te llevas un resumen escrito de lo que vimos.",
    "Dejo una practica corta para la semana siguiente.",
]
METODO_NUEVOS = [
    "La primera clase es para conocernos y ver qué necesitás.",
    "Trabajamos con el material de tu curso, no con uno inventado.",
    "Si te trancás entre clase y clase, me escribís y lo vemos.",
    "Cerramos cada clase con un ejercicio para que veas cuánto avanzaste.",
    "Uso pizarra, esquemas y ejemplos de la vida real.",
    "Antes del examen hacemos un simulacro con tiempo.",
]

EPIGRAFES = ["Espacio de clase", "Mi escritorio de trabajo", "La sala donde damos clase", "Rincón de estudio"]

# ---------------------------------------------------------------------------
# Alumnos. Personas inventadas.
# Los doce primeros son los de siempre; los otros 48 se arman con estas listas.
# ---------------------------------------------------------------------------

ESTUDIANTES = [
    # (nombre, apellido, nacimiento, etapa, nivel, centro, barrio)
    ("Mateo", "Lopez", date(2009, 3, 14), "Bachillerato", "5.o", "Liceo Bauzá", "Cordón"),
    ("Emma", "Gonzalez", date(2010, 7, 2), "Bachillerato", "4.o", "Liceo N 8", "Pocitos"),
    ("Thiago", "Ramirez", date(2011, 11, 20), "Ciclo básico", "3.o", "IAVA", "Centro"),
    ("Isabella", "Suarez", date(2012, 1, 9), "Ciclo básico", "2.o", "Liceo 14", "La Blanqueada"),
    ("Bruno", "Mendez", date(2008, 5, 30), "Bachillerato", "6.o", "IAVA", "Tres Cruces"),
    ("Julieta", "Castro", date(2007, 9, 12), "Examen de ingreso", None, None, "Punta Carretas"),
    ("Santiago", "Vazquez", date(2005, 2, 25), "Universidad", "2.o", "Facultad de Ingeniería", "Parque Rodó"),
    ("Martina", "Olivera", date(2004, 12, 3), "Universidad", "3.o", "Facultad de Ingeniería", "Cordón"),
    ("Agustin", "Nunez", date(2009, 8, 17), "UTU", "2.o", "UTU Buceo", "Buceo"),
    ("Catalina", "Rios", date(2010, 4, 6), "Bachillerato", "4.o", "Liceo N 8", "Pocitos"),
    ("Benjamin", "Cabrera", date(2006, 6, 21), "Universidad", "1.o", "Facultad de Ingeniería", "Malvín"),
    ("Paula", "Dominguez", date(2011, 10, 28), "Ciclo básico", "3.o", "Liceo Bauzá", "Unión"),
]

NOMBRES_ALUMNOS = [
    "Lucas", "Valentina", "Joaquín", "Renata", "Facundo", "Micaela", "Tomás", "Florencia",
    "Ignacio", "Agustina", "Franco", "Camila", "Felipe", "Victoria", "Gonzalo", "Josefina",
    "Nicolás", "Lola", "Matías", "Antonella", "Santino", "Delfina", "Lautaro", "Guadalupe",
    "Maximiliano", "Pilar", "Diego", "Abril", "Bautista", "Mía", "Emiliano", "Clara",
    "Federico", "Jazmín", "Manuel", "Rocío", "Ramiro", "Lucía", "Alejo", "Sol",
    "Juan Cruz", "Milagros", "Gaspar", "Candela", "Leandro", "Morena", "Simón", "Zoe",
]
APELLIDOS_ALUMNOS = [
    "Fernández", "Rodríguez", "González", "Pérez", "Silva", "Sosa", "Martínez", "López",
    "Méndez", "Díaz", "Romero", "Cabrera", "Núñez", "Morales", "Suárez", "Acosta", "Ramírez",
    "Correa", "Olivera", "Pereira", "Viera", "Castro", "Ferreira", "De León", "Machado",
    "Benítez", "Duarte", "Larrosa", "Techera", "Bentancor",
]

# Cuantos de los 48 nuevos hay de cada etapa, y la edad con la que se arranca
# cada una (el primer anio). El nivel suma uno por anio.
REPARTO_ETAPAS = [(CB, 12), (BACH, 17), (UTU, 6), (UNI, 9), (EXAMEN, 4)]
EDAD_INICIAL = {CB: 12, BACH: 15, UTU: 15, UNI: 18, EXAMEN: 18}

# Para el adulto responsable de los menores (ver usuario.fecha_nacimiento).
ADULTOS = ["Ana", "Carlos", "Laura", "Jorge", "Patricia", "Fernando"]

CALLES = ["Av. 18 de Julio", "Bulevar Artigas", "Av. Italia", "Canelones", "Colonia", "Av. Brasil"]

# Numeros de prueba publicos de las pasarelas (Visa, Mastercard y uno que
# no es de ninguna de las dos, que sale como "Otra"). NUNCA uno real: ver
# pagos/modelos.py. Ninguno termina en 0000, que es el que rechaza el cobro.
TARJETAS_DE_PRUEBA = [
    "4111111111111111",
    "5555555555554444",
    "4012888888881881",
    "5105105105105100",
    "6011111111111117",
]

# ---------------------------------------------------------------------------
# Lo que dicen las clases, las resenas y los mensajes.
# ---------------------------------------------------------------------------

# El tema de cada clase sale de la materia: "tema: funciones exponenciales".
TEMAS_POR_MATERIA = {
    "Matemática": ["Funciones exponenciales", "Derivadas", "Ecuaciones de segundo grado", "Trigonometría",
                   "Límites", "Probabilidad", "Integrales", "Geometría analítica"],
    "Física": ["Cinemática", "Leyes de Newton", "Trabajo y energía", "Electrostática", "Circuitos eléctricos",
               "Óptica"],
    "Química": ["Estequiometría", "Tabla periódica", "Enlaces químicos", "Soluciones", "Química orgánica",
                "Equilibrio químico"],
    "Idioma Español": ["Ortografía y acentuación", "Análisis sintáctico", "Comprensión lectora",
                       "Textos argumentativos"],
    "Inglés": ["Present perfect", "Reading comprehension", "Listening para el examen", "Writing: essays",
               "Conditionals", "Speaking"],
    "Historia": ["Revolución Francesa", "Historia uruguaya del siglo XIX", "Primera Guerra Mundial",
                 "Guerra Fría", "Dictadura y transición democrática"],
    "Biología": ["Célula", "Genética", "Evolución", "Sistema nervioso", "Ecología"],
    "Literatura": ["Análisis de poemas", "El Quijote", "Generación del 900", "Realismo mágico",
                   "Cómo escribir un ensayo"],
    "Geografía": ["Climas del mundo", "Cartografía", "Población y migraciones", "Geografía del Uruguay"],
    "Dibujo": ["Perspectiva", "Vistas y cortes", "Geometría descriptiva", "Croquis a mano alzada"],
    "Filosofía": ["Platón y la caverna", "Descartes", "Ética", "Lógica proposicional"],
    "Economía": ["Oferta y demanda", "Elasticidad", "Macroeconomía básica", "Inflación"],
    "Contabilidad": ["Asientos contables", "Balance general", "Estado de resultados", "Costos"],
    "Programación": ["Variables y condicionales", "Bucles", "Funciones", "Listas y diccionarios",
                     "Recursión", "Programación orientada a objetos"],
    "Francés": ["Passé composé", "Compréhension orale", "Vocabulario de viaje", "Subjonctif"],
    "Portugués": ["Verbos irregulares", "Conversación", "Preparación del Celpe-Bras", "Pronunciación"],
}

MOTIVOS_CANCELACION = [
    "Me surgio un parcial ese dia.",
    "Estoy enfermo, lo pasamos para otra semana.",
    "Tuve un imprevisto familiar.",
    "Se me superpuso con un turno medico.",
    "Me cambiaron el horario del trabajo.",
]

# Los bloqueos fijos de P3: (profeN, dias habiles desde hoy, desde, hasta, motivo).
# Los usa verificar_p3.py. Las clases de los seeds se ubican fuera de ellos.
PLAN_BLOQUEOS = [
    (1, 8, time(14), time(16), "Turno medico"),
    (2, 9, time(15), time(21), "Mesa de examen en el liceo"),
    (3, 10, time(0), time(23, 59), "Congreso de docentes"),
]

MOTIVOS_BLOQUEO_DIA = ["Viaje a Buenos Aires", "Congreso de educación", "Mesa de examen en el liceo",
                       "Casamiento de un amigo"]
MOTIVOS_BLOQUEO_RATO = ["Turno médico", "Reunión de profesores", "Trámite en el banco", "Parcial en facultad"]

# Resenas por puntaje. Una de cada tantas va sin texto (solo las estrellas).
RESENAS_AL_PROFESOR = {
    5: ["Explica re claro y tiene mucha paciencia. Salvé el parcial gracias a sus clases.",
        "Excelente, súper puntual y con muy buen material.",
        "Las clases se pasan volando. Entendí todo lo que no entendía en el liceo.",
        "Muy buena onda. Siempre deja ejercicios para practicar en la semana.",
        "La mejor que tuve, la recomiendo cien por ciento.",
        "Muy ordenado: cada clase arranca por lo que más te cuesta."],
    4: ["Muy buenas clases, a veces se extiende un poco con los ejemplos.",
        "Explica bien, me hubiera gustado un poco más de práctica.",
        "Buen lugar, cómodo y tranquilo. Me ayudó mucho con el examen.",
        "Recomendable. Le cuesta un poco responder los mensajes, pero las clases valen la pena."],
    3: ["Sabe mucho pero va un poco rápido.",
        "Correcto, cumple. Le faltaría dejar más material.",
        "Las clases están bien, pero llegó tarde un par de veces."],
    2: ["No me terminó de servir, explicaba muy rápido.",
        "Canceló dos veces sobre la hora."],
    1: ["No apareció a la clase y tardó días en responder."],
}
RESENAS_AL_ALUMNO = {
    5: ["Muy comprometido, siempre viene con los ejercicios hechos.",
        "Excelente actitud: pregunta todo y avanza muchísimo.",
        "Muy responsable y puntual. Da gusto trabajar así."],
    4: ["Muy buen alumno. A veces le cuesta concentrarse, pero mejora mucho.",
        "Viene con dudas concretas, así se aprovecha la clase."],
    3: ["Le falta practicar entre clase y clase.",
        "Cancela seguido, pero cuando viene trabaja bien."],
    2: ["Llegó tarde varias veces y sin el material."],
    1: ["No vino a la clase y no avisó."],
}

CONTEXTOS = [
    "Tengo parcial en dos semanas.",
    "Me está costando bastante este año.",
    "Quiero prepararme bien para el examen.",
    "Necesito reforzar antes del cierre del semestre.",
    "Me recomendó una compañera.",
]
RESPUESTAS_PRIMERA = [
    "Perfecto, eso lo trabajamos bien. Fijate en mi agenda y reservá el horario que te quede cómodo.",
    "Dale, traé el práctico y arrancamos por lo que más te cueste.",
    "Buenísimo. Reservá cuando quieras y en la primera clase vemos dónde estás.",
]
DESPUES_DE_CLASE = [
    "¡Buen trabajo hoy, {alumno}! Te dejé ejercicios de {tema} para practicar.",
    "Muy bien hoy. Para la próxima repasá {tema} y traé las dudas.",
    "Gracias por la clase de hoy, se nota el avance. Seguí con {tema} que vas bien.",
]
RESPUESTAS_ALUMNO = [
    "¡Gracias, profe! Los hago para la próxima.",
    "¡Gracias! Ahora me quedó mucho más claro.",
    "Buenísimo, gracias por la paciencia.",
]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


# ===========================================================================
# El sembrado, en el orden en que lo corre main()
# ===========================================================================

def limpiar(db) -> None:
    """Vacia las 24 tablas.

    Un solo TRUNCATE con todas juntas: PostgreSQL resuelve solo el orden de las
    claves foraneas, y RESTART IDENTITY reinicia los ids, asi profe1 tiene el
    mismo id en todas las maquinas. alembic_version no se toca porque no esta
    en metadata.
    """
    tablas = ", ".join(tabla.name for tabla in metadata.sorted_tables)
    db.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY"))


def sembrar_catalogos(db) -> dict:
    """Carga barrios, materias, etapas, centros, idiomas y parametros.

    Devuelve un diccionario con lo creado (ya con id, por los flush), para que
    las funciones siguientes puedan referenciarlo sin volver a consultar.
    """
    barrios = {
        nombre: Barrio(nombre=nombre, latitud=Decimal(str(lat)), longitud=Decimal(str(lon)))
        for nombre, lat, lon in BARRIOS
    }
    materias = {nombre: Materia(nombre=nombre, nombre_corto=corto) for nombre, corto in MATERIAS}
    etapas = {
        nombre: EtapaEducativa(nombre=nombre, orden=orden, niveles=niveles)
        for nombre, orden, niveles in ETAPAS
    }
    idiomas = {nombre: Idioma(nombre=nombre) for nombre in IDIOMAS}
    db.add_all([*barrios.values(), *materias.values(), *etapas.values(), *idiomas.values()])
    # Los centros necesitan el id del barrio, y no hay relationship() que lo
    # resuelva solo: las FK se declaran por nombre de tabla.
    db.flush()

    azar = random.Random(SEMILLA)
    centros = {}
    for nombre, tipo, barrio in CENTROS:
        latitud, longitud = _cerca(barrios[barrio], azar)
        centros[nombre] = CentroEducativo(
            nombre=nombre,
            tipo=TipoCentro(tipo),
            barrio_id=barrios[barrio].id,
            latitud=latitud,
            longitud=longitud,
        )
    db.add_all(centros.values())

    db.add_all(
        ParametroPlataforma(clave=clave, valor=Decimal(str(valor)), vigente_desde=desde)
        for clave, valor, desde in PARAMETROS
    )
    db.flush()

    # Los que valen hoy (el ultimo que ya empezo de cada clave). Las clases de
    # los seeds son todas de los ultimos meses, asi que les tocan estos.
    hoy = datetime.now(ZONA).date()
    vigentes = {}
    for clave, valor, desde in sorted(PARAMETROS, key=lambda p: p[2]):
        if desde <= hoy:
            vigentes[clave] = Decimal(str(valor))

    return {
        "barrios": barrios,
        "materias": materias,
        "etapas": etapas,
        "centros": centros,
        "idiomas": idiomas,
        "comision": vigentes["comision_servicio"],
        "iva": vigentes["tasa_iva"],
    }


def sembrar_usuarios(db, catalogos: dict) -> dict:
    """Crea los 94 usuarios: 34 profesores y 60 alumnos.

    El orden importa: primero los veinte de siempre (profe1..profe8 quedan con
    los ids 1 a 8 y alumno1..alumno12 con los 9 a 20, como antes) y despues los
    nuevos, para que ningun id de los viejos cambie.
    """
    hoy = datetime.now(ZONA).date()
    # Hasheada UNA sola vez: bcrypt es lento a proposito, y 94 hashes harian
    # que el seed tarde casi un minuto.
    hash_clave = hashear_clave(CLAVE_DE_PRUEBA)
    azar = random.Random(SEMILLA + 1)
    foto_aula = "data:image/jpeg;base64," + base64.b64encode(FOTO_AULA.read_bytes()).decode("ascii")

    estudiantes_datos = ESTUDIANTES + _estudiantes_nuevos(hoy)
    profesores, estudiantes = [], []

    def crear_profesores(desde: int, hasta: int):
        for n in range(desde, hasta + 1):
            profesores.append(
                _crear_profesor(db, n, PROFESORES[n - 1], catalogos, hash_clave, foto_aula, azar)
            )

    def crear_estudiantes(desde: int, hasta: int):
        for n in range(desde, hasta + 1):
            estudiantes.append(
                _crear_estudiante(db, n, estudiantes_datos[n - 1], catalogos, hash_clave, hoy, azar)
            )

    crear_profesores(1, 8)
    crear_estudiantes(1, 12)
    crear_profesores(9, len(PROFESORES))
    crear_estudiantes(13, len(estudiantes_datos))

    db.flush()
    return {"profesores": profesores, "estudiantes": estudiantes}


def sembrar_agenda(db, usuarios: dict) -> None:
    """Carga las franjas semanales de cada profesor y algunos bloqueos.

    Sin franjas, el calendario de 1f sale vacio y no se puede reservar nada.
    Los bloqueos son las excepciones con fecha ("el 12 no puedo"): mas o menos
    un tercio de los profesores tiene alguno en las proximas dos semanas, y
    algunos tambien uno ya pasado.

    Deja en cada profesor sus franjas y sus bloqueos ya armados, para que
    sembrar_clases ponga las clases adentro de las franjas y fuera de los
    bloqueos.
    """
    azar = random.Random(SEMILLA + 2)
    hoy = datetime.now(ZONA).date()

    for profe in usuarios["profesores"]:
        perfil = profe["perfil"]
        profe["franjas"] = [(dia, time(desde), time(hasta)) for dia, desde, hasta in HORARIOS[profe["horario"]]]
        db.add_all(
            FranjaDisponibilidad(
                perfil_profesor_id=perfil.id,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                modalidad=perfil.modalidad,
            )
            for dia, inicio, fin in profe["franjas"]
        )

        fijos = [b for b in PLAN_BLOQUEOS if b[0] == profe["numero"]]
        if fijos:
            # profe1, profe2 y profe3 tienen los bloqueos fijos de P3 y ninguno
            # mas: verificar_p3.py cuenta con ellos (por ejemplo, que el de
            # profe1 caiga adentro de su franja y sea el unico que tiene).
            bloqueos = [
                (datetime.combine(_dia_habil(hoy, dias), desde, ZONA),
                 datetime.combine(_dia_habil(hoy, dias), hasta, ZONA), motivo)
                for _, dias, desde, hasta, motivo in fijos
            ]
        else:
            bloqueos = _bloqueos_al_azar(profe, hoy, azar)

        profe["bloqueos"] = []
        for inicio, fin, motivo in bloqueos:
            db.add(Bloqueo(perfil_profesor_id=perfil.id, inicio=inicio, fin=fin, motivo=motivo))
            profe["bloqueos"].append((inicio, fin))
    db.flush()


def _bloqueos_al_azar(profe: dict, hoy: date, azar: random.Random) -> list[tuple]:
    """Ninguno, uno o dos bloqueos: uno en las proximas dos semanas y otro ya pasado.

    La mitad son un rato adentro de la franja de ese dia ("Turno medico") y la
    otra mitad, el dia entero ("Viaje a Buenos Aires").
    """
    dias = []
    if azar.random() < 0.4:
        dias.append(hoy + timedelta(days=azar.randint(2, DIAS_POR_DELANTE)))
    if azar.random() < 0.3:
        dias.append(hoy - timedelta(days=azar.randint(5, 60)))
    bloqueos = []
    for dia in dias:
        tramos = [(a, b) for d, a, b in profe["franjas"] if d == _dia_semana(dia)]
        if tramos and azar.random() < 0.5:
            desde, _ = azar.choice(tramos)
            inicio = datetime.combine(dia, desde, ZONA)
            bloqueos.append((inicio, inicio + timedelta(hours=2), azar.choice(MOTIVOS_BLOQUEO_RATO)))
        else:
            inicio = datetime.combine(dia, time(0), ZONA)
            bloqueos.append((inicio, inicio + timedelta(days=1), azar.choice(MOTIVOS_BLOQUEO_DIA)))
    return bloqueos


def sembrar_clases(db, usuarios: dict, catalogos: dict) -> dict:
    """Crea la historia de clases de cada profesor publicado, con sus cobros.

    Recorre dia por dia desde hace SEMANAS_DE_HISTORIA semanas hasta dentro de
    DIAS_POR_DELANTE dias, y en los dias que el profesor atiende le pone una o
    dos clases con alumnos de su "grupo" (los que estudian una etapa que el
    da). Con las reglas de un profesor real:

      - la clase entra entera en una franja de ese dia,
      - no se pisa con otra del mismo profesor (ni con su descanso), ni con un
        bloqueo, ni con otra clase del mismo alumno,
      - respeta el tope de clases por dia y el aviso minimo del profesor,
      - una sola aprobada por dia: la restriccion EXCLUDE no salta, y
        verificar_p4.py busca una aprobada sin otra cerca.

    El estado sale de cuando cae: lo que ya paso esta dictado (y algo
    cancelado o no asistido), lo que viene esta aprobado o pendiente. Ademas,
    cada profesor rechazo alguna solicitud: el cobro liberado queda sin clase.

    Devuelve las clases agrupadas por par (alumno, profesor): las usan las
    resenas y los mensajes.
    """
    ahora = datetime.now(ZONA)
    hoy = ahora.date()
    azar = random.Random(SEMILLA + 3)
    comision, iva = catalogos["comision"], catalogos["iva"]

    ocupado_alumno = defaultdict(list)  # usuario_id del alumno -> [(inicio, fin)]
    clases_por_alumno = Counter()
    pares = {}  # (alumno usuario_id, profesor usuario_id) -> {"alumno", "profe", "clases"}

    publicados = [p for p in usuarios["profesores"] if p["perfil"].estado_ficha == EstadoFicha.publicada]
    agendas = []
    for profe in publicados:
        grupo, pesos = _grupo_del_profesor(profe, usuarios["estudiantes"], azar)
        agendas.append({"profe": profe, "grupo": grupo, "pesos": pesos, "plan": [],
                        "ocupado": {"profe": [], "por_dia": Counter()}})

    # --- 1. Cuando y con quien --------------------------------------------
    # En dos tandas: primero las proximas dos semanas de TODOS los profesores,
    # y despues la historia, del dia mas reciente al mas viejo. Asi, cuando un
    # alumno o un profesor llega a su tope, lo que se pierde es la historia
    # mas vieja y no lo que viene.
    proximos = [hoy + timedelta(days=d) for d in range(DIAS_POR_DELANTE + 1)]
    pasados = [hoy - timedelta(days=d) for d in range(1, SEMANAS_DE_HISTORIA * 7 + 1)]
    for dias in (proximos, pasados):
        for agenda in agendas:
            profe, plan = agenda["profe"], agenda["plan"]
            # El futuro se llena un poco mas: la agenda de las proximas
            # semanas tiene que verse con movimiento.
            probabilidad = 0.2 + 0.12 * profe["popularidad"] + (0.25 if dias is proximos else 0)
            for dia in dias:
                tramos = [(a, b) for d, a, b in profe["franjas"] if d == _dia_semana(dia)]
                if not tramos or azar.random() >= probabilidad:
                    continue
                for _ in range(1 if azar.random() < 0.7 else 2):
                    if len(plan) >= MAX_CLASES_PROFESOR:
                        break
                    lugar = _ubicar_clase(profe, dia, tramos, agenda["grupo"], agenda["pesos"],
                                          agenda["ocupado"], ocupado_alumno, clases_por_alumno, ahora, azar)
                    if lugar:
                        plan.append(lugar)

    for agenda in agendas:
        profe, plan, grupo = agenda["profe"], agenda["plan"], agenda["grupo"]
        perfil = profe["perfil"]

        # --- 2. El estado de cada una -------------------------------------
        plan.sort(key=lambda p: p["inicio"])
        dias_con_aprobada = set()
        for p in plan:
            if p["fin"] <= ahora:
                r = azar.random()
                p["estado"] = (EstadoClase.dictada if r < 0.84
                               else EstadoClase.cancelada if r < 0.94 else EstadoClase.no_asistida)
            elif p["inicio"].date() not in dias_con_aprobada and (not dias_con_aprobada or azar.random() < 0.55):
                p["estado"] = EstadoClase.aprobada
                dias_con_aprobada.add(p["inicio"].date())
            else:
                p["estado"] = EstadoClase.pendiente if azar.random() < 0.88 else EstadoClase.cancelada
        _asegurar_aprobada_y_pendiente(plan, ahora)

        # --- 3. Las filas: clase y cobro ----------------------------------
        filas = [(p, *_armar_clase(profe, p, catalogos, comision, iva, ahora, azar)) for p in plan]
        db.add_all(clase for _, clase, _ in filas)
        db.flush()  # los cobros y el enlace de la videollamada necesitan clase.id

        for p, clase, momentos in filas:
            if clase.modalidad == Modalidad.online:
                # El mismo enlace que arma crear() en clases/logica.py.
                clase.ubicacion = f"https://meet.exonero.test/clase-{clase.id}"
            db.add(_cobro_de(clase, p["alumno"]["tarjeta"], momentos, azar))
            clave = (p["alumno"]["usuario"].id, profe["usuario"].id)
            pares.setdefault(clave, {"alumno": p["alumno"], "profe": profe, "clases": []})
            pares[clave]["clases"].append(clase)

        perfil.clases_dictadas = sum(1 for _, clase, _ in filas if clase.estado == EstadoClase.dictada)

        # --- 4. Solicitudes rechazadas: el cobro liberado queda sin clase ---
        for _ in range(azar.choice([0, 1, 1, 2])):
            db.add(_cobro_rechazado(profe, azar.choice(grupo), comision, iva, ahora, azar))

    db.flush()
    return pares


def sembrar_resenas(db, pares: dict) -> None:
    """Resenas en los dos sentidos, y el promedio en cada perfil.

    Solo entre quienes tuvieron al menos una clase dictada (es lo que va a
    exigir resenas.tuvieron_clase), y una por par y por sentido (el UNIQUE de
    la tabla). Cada persona tiene una "calidad" de fondo y las estrellas salen
    alrededor de ella: asi hay profesores muy bien puntuados y otros no tanto,
    y el ranking de 1a (que pide 5 resenas como minimo) tiene de donde elegir.

    El puntaje promedio y la cantidad de cada perfil (estan desnormalizados,
    ver la seccion 4 de la documentacion) los calcula resenas.recalcular(), la
    misma funcion que usa la API: es la unica puerta por la que cambian.
    """
    ahora = datetime.now(ZONA)
    azar = random.Random(SEMILLA + 4)
    calidad = {}
    destinatarios = set()

    for clave in sorted(pares):
        par = pares[clave]
        dictadas = sorted((c for c in par["clases"] if c.estado == EstadoClase.dictada), key=lambda c: c.inicio)
        if not dictadas:
            continue
        alumno, profe = par["alumno"], par["profe"]

        sentidos = []
        if azar.random() < 0.8:
            sentidos.append((alumno, profe, SentidoResena.alumno_a_profesor, RESENAS_AL_PROFESOR, (3.7, 4.95)))
        if azar.random() < 0.5:
            sentidos.append((profe, alumno, SentidoResena.profesor_a_alumno, RESENAS_AL_ALUMNO, (3.6, 5.0)))
        for autor, destinatario, sentido, textos, rango in sentidos:
            destino_id = destinatario["usuario"].id
            if destino_id not in calidad:
                calidad[destino_id] = azar.uniform(*rango)
            puntaje = max(1, min(5, round(azar.gauss(calidad[destino_id], 0.7))))
            cuando = min(dictadas[0].fin + timedelta(hours=azar.randint(2, 96)), ahora)
            db.add(Resena(
                autor_id=autor["usuario"].id,
                destinatario_id=destino_id,
                sentido=sentido,
                puntaje=puntaje,
                texto=None if azar.random() < 0.15 else azar.choice(textos[puntaje]),
                creado_el=cuando,
            ))
            destinatarios.add(destino_id)

    db.flush()  # recalcular() lee la tabla: las resenas tienen que estar escritas
    for usuario_id in sorted(destinatarios):
        resenas.recalcular(db, usuario_id)
    db.flush()


def sembrar_mensajes(db, pares: dict, usuarios: dict, catalogos: dict) -> None:
    """Conversaciones entre alumnos y profesores, algunas con mensajes sin leer.

    Casi todos los pares que tuvieron clase tienen su hilo, con una charla que
    sigue lo que paso: la consulta antes de reservar, donde es la clase, el
    "buen trabajo hoy" despues de una dictada, el aviso de una cancelacion y
    la pregunta por la proxima. Ademas hay consultas de alumnos que todavia no
    reservaron, algunas sin contestar.

    Lo ultimo de una charla reciente puede quedar sin leer (leido_el NULL):
    es lo que cuenta el numerito de mensajes de la barra de arriba.
    """
    ahora = datetime.now(ZONA)
    azar = random.Random(SEMILLA + 5)
    nombres = {
        "materias": {m.id: nombre for nombre, m in catalogos["materias"].items()},
        "etapas": {e.id: nombre for nombre, e in catalogos["etapas"].items()},
    }
    charlas = []  # (alumno, profe, [(autor_id, texto, cuando)], es de un usuario de prueba)

    # verificar_p3.py abre, del lado del profesor, un hilo de profe1 con un
    # alumno suyo que todavia no tiene charla: se deja uno asi (el de id mas
    # alto que no sea alumno1).
    de_profe1 = sorted(clave for clave, par in pares.items()
                       if par["profe"]["numero"] == 1 and par["alumno"]["numero"] != 1)
    sin_charla = set(de_profe1[-1:])

    for clave in sorted(pares):
        if clave in sin_charla:
            continue
        par = pares[clave]
        # Los usuarios de prueba del login (alumno1 y profe1) tienen siempre su
        # charla, y es mas probable que les quede algo sin leer: es lo primero
        # que se ve al entrar con ellos.
        de_prueba = par["alumno"]["numero"] == 1 or par["profe"]["numero"] == 1
        if de_prueba or azar.random() < 0.85:
            charlas.append((par["alumno"], par["profe"], _charla(par, nombres, ahora, azar), de_prueba))

    # Consultas de quien todavia no reservo.
    publicados = [p for p in usuarios["profesores"] if p["perfil"].estado_ficha == EstadoFicha.publicada]
    ya_hablaron = set(pares)
    for _ in range(25):
        alumno, profe = azar.choice(usuarios["estudiantes"]), azar.choice(publicados)
        clave = (alumno["usuario"].id, profe["usuario"].id)
        if clave in ya_hablaron:
            continue
        ya_hablaron.add(clave)
        charlas.append((alumno, profe, _consulta(alumno, profe, ahora, azar), False))

    hilos = []
    for alumno, profe, mensajes, de_prueba in charlas:
        # verificar_p3.py abre desde cero el hilo de alumno3 con profe1 (y
        # comprueba que antes no existia): ese par no tiene que tener charla.
        if (alumno["numero"], profe["numero"]) == (3, 1):
            continue
        mensajes = sorted((m for m in mensajes if m[2] <= ahora), key=lambda m: m[2])
        if not mensajes:
            continue
        hilo = Hilo(
            estudiante_id=alumno["usuario"].id,
            profesor_id=profe["usuario"].id,
            ultimo_mensaje_el=mensajes[-1][2],
            creado_el=mensajes[0][2],
        )
        hilos.append((hilo, mensajes, de_prueba))
    db.add_all(hilo for hilo, _, _ in hilos)
    db.flush()  # los mensajes necesitan hilo.id

    for hilo, mensajes, de_prueba in hilos:
        # Lo ultimo de una charla de estos dias puede estar sin leer. Si la
        # misma persona escribio dos seguidos al final, quedan los dos.
        ultimo_autor, ultimo_cuando = mensajes[-1][0], mensajes[-1][2]
        sin_leer = ahora - ultimo_cuando < timedelta(days=4) and azar.random() < (0.9 if de_prueba else 0.6)
        for k, (autor_id, contenido, cuando) in enumerate(mensajes):
            al_final = all(m[0] == ultimo_autor for m in mensajes[k:])
            leido = None if (sin_leer and al_final) else min(cuando + timedelta(minutes=azar.randint(3, 240)), ahora)
            db.add(Mensaje(
                hilo_id=hilo.id,
                autor_id=autor_id,
                contenido=contenido,
                enviado_el=cuando,
                leido_el=leido,
                creado_el=cuando,
            ))
    db.flush()


# ===========================================================================
# Auxiliares: las personas
# ===========================================================================

def _crear_profesor(db, n: int, datos: dict, catalogos: dict, hash_clave: str, foto_aula: str,
                    azar: random.Random) -> dict:
    """Crea el usuario profeN con su perfil y toda su oferta."""
    usuario = Usuario(
        correo=f"profe{n}@example.com",
        hash_clave=hash_clave,
        nombre=datos["nombre"],
        apellido=datos["apellido"],
        documento=_documento(n),
        telefono=_telefono(n),
        # Los de siempre conservan su fecha; los nuevos nacieron entre 1970 y 1998.
        fecha_nacimiento=date(1978 + 2 * n, n, 10 + n) if n <= 8 else date(1970 + n % 29, n % 12 + 1, 1 + n % 27),
        rol=Rol.profesor,
    )
    db.add(usuario)
    db.flush()  # el perfil necesita usuario.id

    barrios = catalogos["barrios"]
    barrio = barrios[datos["barrio"]]
    latitud, longitud = _cerca(barrio, azar)
    a_domicilio = datos["lugar"] in (LugarClase.a_domicilio, LugarClase.ambos)
    # Las reglas de la seccion "Reglas" de 1j. Los de siempre usan los valores
    # por defecto de la tabla; se escriben igual, porque sembrar_clases las lee.
    reglas = {"descanso_min": 0, "aviso_minimo_horas": 12, **datos.get("reglas", {})}
    duracion_max = reglas.pop("duracion_max", datos.get("duracion_max", 120))
    if n <= 8:
        # Los de siempre, con la biografia de siempre.
        biografia = (
            f"Doy clases particulares hace {datos['anios']} anios. "
            f"{datos['titulo']}. Me adapto al ritmo de cada alumno y "
            "trabajo con el material que usan en clase."
        )
    else:
        biografia = BIOGRAFIAS[n % len(BIOGRAFIAS)].format(
            anios=datos["anios"], titulo=datos["titulo"],
            etapas=", ".join(_etapa_en_texto(e) for e in datos["etapas"]),
        )
    perfil = PerfilProfesor(
        usuario_id=usuario.id,
        titular=datos["titular"],
        biografia=biografia,
        titulo_habilitante=datos["titulo"],
        anios_experiencia=datos["anios"],
        barrio_id=barrio.id,
        direccion_espacio=datos["direccion"],
        latitud=latitud,
        longitud=longitud,
        modalidad=datos["modalidad"],
        lugar_clase=datos["lugar"],
        costo_traslado=Decimal("150") if a_domicilio else Decimal("0"),
        precio_hora_presencial=_precio(datos["precio_presencial"]),
        precio_hora_online=_precio(datos["precio_online"]),
        duracion_min=60,
        duracion_max=duracion_max,
        estado_ficha=datos["ficha"],
        **reglas,
    )
    db.add(perfil)
    db.flush()  # las siete tablas de la oferta necesitan perfil.id

    materias = [catalogos["materias"][m].id for m in datos["materias"]]
    etapas = [catalogos["etapas"][e].id for e in datos["etapas"]]
    duraciones = [m for m in (60, 90, 120) if m <= duracion_max]
    db.add_all(ProfesorMateria(perfil_profesor_id=perfil.id, materia_id=m) for m in materias)
    db.add_all(
        ProfesorEtapa(
            perfil_profesor_id=perfil.id,
            etapa_id=catalogos["etapas"][e].id,
            programa="Plan 2006 y reformulacion 2023" if e in (CB, BACH) else None,
        )
        for e in datos["etapas"]
    )
    db.add_all(
        ProfesorIdioma(perfil_profesor_id=perfil.id, idioma_id=catalogos["idiomas"][i].id)
        for i in datos["idiomas"]
    )
    if a_domicilio:
        # Su barrio y los dos siguientes de la lista.
        nombres = [b[0] for b in BARRIOS]
        desde = nombres.index(datos["barrio"])
        zonas = [nombres[(desde + k) % len(nombres)] for k in range(3)]
        db.add_all(ProfesorZona(perfil_profesor_id=perfil.id, barrio_id=barrios[z].id) for z in zonas)
    db.add_all(ProfesorDuracion(perfil_profesor_id=perfil.id, minutos=m) for m in duraciones)
    if n <= 8:
        puntos = [METODO[(n + k) % len(METODO)] for k in range(3)]
    else:
        todos = METODO + METODO_NUEVOS
        puntos = [todos[(n * 3 + k) % len(todos)] for k in range(3)]
    db.add_all(PuntoMetodo(perfil_profesor_id=perfil.id, texto=texto, orden=k) for k, texto in enumerate(puntos))
    # La foto del lugar: la de profe1 de siempre, y la misma foto de ejemplo
    # para algunos de los nuevos que reciben en su espacio (no hay otra).
    con_foto = n == 1 or (n > 8 and datos["direccion"] and datos["lugar"] in (ESPACIO, AMBOS) and n % 3 == 0)
    if con_foto:
        db.add(FotoLugar(
            perfil_profesor_id=perfil.id,
            imagen_base64=foto_aula,
            epigrafe="Espacio de clase" if n == 1 else EPIGRAFES[n % len(EPIGRAFES)],
            orden=0,
            es_portada=True,
        ))

    return {
        "numero": n,
        "usuario": usuario,
        "perfil": perfil,
        "materias": materias,
        "materias_nombres": list(datos["materias"]),
        "etapas": etapas,
        "duraciones": duraciones,
        "horario": datos.get("horario") or ("original_par" if n % 2 == 1 else "original_impar"),
        # Que tan seguido tiene clases: 1, 2 o 3. profe1 queda en 2.
        "popularidad": 1 + (n * 7) % 3,
    }


def _crear_estudiante(db, n: int, datos: tuple, catalogos: dict, hash_clave: str, hoy: date,
                      azar: random.Random) -> dict:
    """Crea el usuario alumnoN con su perfil y sus tarjetas."""
    nombre, apellido, nacimiento, etapa, nivel, centro, barrio = datos
    barrios = catalogos["barrios"]
    usuario = Usuario(
        correo=f"alumno{n}@example.com",
        hash_clave=hash_clave,
        nombre=nombre,
        apellido=apellido,
        documento=_documento(100 + n),
        telefono=_telefono(100 + n),
        fecha_nacimiento=nacimiento,
        rol=Rol.estudiante,
    )
    db.add(usuario)
    db.flush()

    menor = _edad(nacimiento, hoy) < 18
    latitud, longitud = _cerca(barrios[barrio], azar)
    perfil = PerfilEstudiante(
        usuario_id=usuario.id,
        etapa_id=catalogos["etapas"][etapa].id,
        nivel=nivel,  # solo el anio ("5.o"); el frontend arma "5.o de Bachillerato"
        centro_id=catalogos["centros"][centro].id if centro else None,
        barrio_id=barrios[barrio].id,
        direccion=f"{CALLES[n % len(CALLES)]} {1000 + n * 37}",
        latitud=latitud,
        longitud=longitud,
        # Obligatorio para los menores de edad.
        adulto_nombre=f"{ADULTOS[n % len(ADULTOS)]} {apellido}" if menor else None,
        adulto_telefono=_telefono(200 + n) if menor else None,
    )
    titular = f"{nombre} {apellido}".upper()
    if n <= 12:
        # Los de siempre: una sola tarjeta, la de prueba de siempre.
        tarjetas = [Tarjeta(usuario_id=usuario.id, numero="4111111111111111", titular=titular,
                            vence_mes=12, vence_anio=hoy.year + 3, ccv="123")]
    else:
        tarjetas = _tarjetas_nuevas(usuario.id, titular, hoy, azar)
    db.add_all([perfil, *tarjetas])
    # La primera es con la que paga sus clases.
    return {"numero": n, "usuario": usuario, "perfil": perfil, "tarjeta": tarjetas[0]}


def _estudiantes_nuevos(hoy: date) -> list[tuple]:
    """Los 48 alumnos nuevos, con la misma forma que ESTUDIANTES.

    La edad sale de la etapa y el nivel (uno de 5.o de Bachillerato tiene 16 o
    17 anios), y el centro, de la etapa: liceo para ciclo basico y
    bachillerato, UTU para UTU y facultad para universidad.
    """
    azar = random.Random(SEMILLA + 6)
    centros = {tipo: [c[0] for c in CENTROS if c[1] == tipo] for tipo in ("liceo", "utu", "facultad")}
    centro_de = {CB: "liceo", BACH: "liceo", UTU: "utu", UNI: "facultad"}
    niveles = {nombre: lista for nombre, _, lista in ETAPAS}
    barrios = [b[0] for b in BARRIOS]

    etapas = [etapa for etapa, cantidad in REPARTO_ETAPAS for _ in range(cantidad)]
    azar.shuffle(etapas)
    nuevos = []
    for k, etapa in enumerate(etapas):
        nivel = azar.choice(niveles[etapa]) if niveles[etapa] else None
        edad = EDAD_INICIAL[etapa] + (niveles[etapa].index(nivel) if nivel else azar.randint(0, 1))
        nacimiento = date(hoy.year - edad - 1, azar.randint(1, 12), azar.randint(1, 28))
        centro = azar.choice(centros[centro_de[etapa]]) if etapa in centro_de else None
        nuevos.append((
            NOMBRES_ALUMNOS[k % len(NOMBRES_ALUMNOS)],
            azar.choice(APELLIDOS_ALUMNOS),
            nacimiento,
            etapa,
            nivel,
            centro,
            azar.choice(barrios),
        ))
    return nuevos


def _tarjetas_nuevas(usuario_id: int, titular: str, hoy: date, azar: random.Random) -> list:
    """Entre una y tres tarjetas: la que usa, a veces otra, y alguna vencida o dada de baja.

    "Medios de pago" de 1e muestra las activas (y marca las vencidas); las dadas
    de baja no salen, pero los cobros viejos las siguen nombrando.
    """
    numeros = azar.sample(TARJETAS_DE_PRUEBA, 3)

    def tarjeta(numero, vence_anio, activa=True):
        return Tarjeta(usuario_id=usuario_id, numero=numero, titular=titular,
                       vence_mes=azar.randint(1, 12), vence_anio=vence_anio,
                       ccv=str(azar.randint(100, 999)), activa=activa)

    tarjetas = [tarjeta(numeros[0], hoy.year + azar.randint(1, 4))]
    if azar.random() < 0.35:
        tarjetas.append(tarjeta(numeros[1], hoy.year + azar.randint(1, 4)))
    if azar.random() < 0.15:
        tarjetas.append(tarjeta(numeros[2], hoy.year - 1))                # vencida
    elif azar.random() < 0.15:
        tarjetas.append(tarjeta(numeros[2], hoy.year + 2, activa=False))  # dada de baja
    return tarjetas


# ===========================================================================
# Auxiliares: las clases y la plata
# ===========================================================================

def _grupo_del_profesor(profe: dict, estudiantes: list, azar: random.Random) -> tuple[list, list]:
    """Los alumnos que toman clase con este profesor, y que tan seguido.

    Se eligen entre los que estudian una etapa que el da (si no alcanzan, se
    completa con otros). Los tres primeros vuelven mucho mas seguido: son los
    alumnos recurrentes de 1d.
    """
    etapas = set(profe["etapas"])
    # alumno1 es alumno fijo de profe1: los dos usuarios de prueba del login
    # tienen que tener clases entre ellos.
    fijos = [a for a in estudiantes if a["numero"] == 1] if profe["numero"] == 1 else []
    compatibles = [a for a in estudiantes if a["perfil"].etapa_id in etapas and a not in fijos]
    resto = [a for a in estudiantes if a["perfil"].etapa_id not in etapas and a not in fijos]
    tamanio = 4 + 2 * profe["popularidad"] + azar.randint(0, 2)
    grupo = fijos + azar.sample(compatibles, min(tamanio - len(fijos), len(compatibles)))
    if len(grupo) < tamanio:
        grupo += azar.sample(resto, tamanio - len(grupo))
    pesos = [5 if k < 3 else 1 for k in range(len(grupo))]
    return grupo, pesos


def _ubicar_clase(profe: dict, dia: date, tramos: list, grupo: list, pesos: list, ocupado: dict,
                  ocupado_alumno: dict, clases_por_alumno: Counter, ahora: datetime,
                  azar: random.Random) -> dict | None:
    """Busca un rato libre ese dia y un alumno que pueda. None si no encuentra.

    Prueba unas cuantas veces con otra duracion, otra franja, otro horario y
    otro alumno. Si encuentra, marca el rato como ocupado para los dos.
    """
    perfil = profe["perfil"]
    if perfil.max_clases_dia and ocupado["por_dia"][dia] >= perfil.max_clases_dia:
        return None
    descanso = timedelta(minutes=perfil.descanso_min)
    aviso = timedelta(hours=perfil.aviso_minimo_horas)

    for _ in range(8):
        duracion = azar.choice(profe["duraciones"])
        desde, hasta = azar.choice(tramos)
        # Los inicios posibles, cada media hora, para que entre entera en la franja.
        inicios = []
        t = datetime.combine(dia, desde, ZONA)
        tope = datetime.combine(dia, hasta, ZONA) - timedelta(minutes=duracion)
        while t <= tope:
            inicios.append(t)
            t += timedelta(minutes=30)
        if not inicios:
            continue
        inicio = azar.choice(inicios)
        fin = inicio + timedelta(minutes=duracion)
        # Ni una en curso ni una pedida mas sobre la hora que el aviso minimo.
        if fin > ahora and inicio < ahora + aviso:
            continue
        if _se_pisa(inicio - descanso, fin + descanso, ocupado["profe"]) or _se_pisa(inicio, fin, profe["bloqueos"]):
            continue
        alumno = azar.choices(grupo, weights=pesos)[0]
        uid = alumno["usuario"].id
        if clases_por_alumno[uid] >= MAX_CLASES_ALUMNO or _se_pisa(inicio, fin, ocupado_alumno[uid]):
            continue

        ocupado["profe"].append((inicio, fin))
        ocupado["por_dia"][dia] += 1
        ocupado_alumno[uid].append((inicio, fin))
        clases_por_alumno[uid] += 1
        return {"alumno": alumno, "inicio": inicio, "fin": fin, "duracion": duracion}
    return None


def _asegurar_aprobada_y_pendiente(plan: list, ahora: datetime) -> None:
    """Que cada profesor tenga por delante al menos una aprobada y una pendiente.

    Sin pendientes, la bandeja de solicitudes de 1i sale vacia; sin aprobadas,
    no hay "proxima clase" en 1d. Y verificar_p4.py usa una de cada de profe1.
    """
    futuras = [p for p in plan if p["fin"] > ahora]
    aprobadas = [p for p in futuras if p["estado"] == EstadoClase.aprobada]
    pendientes = [p for p in futuras if p["estado"] == EstadoClase.pendiente]
    if not pendientes and len(aprobadas) >= 2:
        aprobadas[-1]["estado"] = EstadoClase.pendiente
    elif not aprobadas and pendientes:
        pendientes[0]["estado"] = EstadoClase.aprobada


def _condiciones(perfil, alumno: dict, azar: random.Random) -> tuple:
    """Modalidad, precio por hora, traslado y ubicacion de una clase concreta.

    Una clase es presencial u online aunque el profesor de las dos. Si es a
    domicilio, se cobra el traslado y la clase es en la casa del alumno.
    """
    if perfil.modalidad == Modalidad.ambas:
        modalidad = azar.choice([Modalidad.presencial, Modalidad.online])
    else:
        modalidad = perfil.modalidad
    if modalidad == Modalidad.online:
        # La ubicacion (el enlace) se arma despues, con el id de la clase.
        return modalidad, perfil.precio_hora_online, Decimal("0"), None
    a_domicilio = perfil.lugar_clase == LugarClase.a_domicilio or (
        perfil.lugar_clase == LugarClase.ambos and azar.random() < 0.5
    )
    traslado = perfil.costo_traslado if a_domicilio else Decimal("0")
    ubicacion = alumno["perfil"].direccion if a_domicilio else perfil.direccion_espacio
    return modalidad, perfil.precio_hora_presencial, traslado, ubicacion


def _armar_clase(profe: dict, p: dict, catalogos: dict, comision: Decimal, iva: Decimal,
                 ahora: datetime, azar: random.Random) -> tuple:
    """La fila de la clase (sin guardar) y los momentos de su historia.

    Los momentos son cuando se pidio, cuando se aprobo y cuando se cancelo:
    los usa el cobro, que guarda un timestamp por cada transicion.
    """
    perfil, alumno = profe["perfil"], p["alumno"]
    modalidad, precio_hora, traslado, ubicacion = _condiciones(perfil, alumno, azar)
    k = azar.randrange(len(profe["materias"]))
    materia_id, materia = profe["materias"][k], profe["materias_nombres"][k]
    etapa_alumno = alumno["perfil"].etapa_id
    etapa_id = etapa_alumno if etapa_alumno in profe["etapas"] else azar.choice(profe["etapas"])

    # La solicitud se hizo unos dias antes, nunca en el futuro; el profesor la
    # aprobo unas horas despues.
    pedida = min(p["inicio"] - timedelta(days=azar.randint(1, 8), hours=azar.randint(0, 12)),
                 ahora - timedelta(minutes=azar.randint(15, 600)))
    aprobada = max(min(pedida + timedelta(minutes=azar.randint(30, 20 * 60)), ahora - timedelta(minutes=1)),
                   pedida + timedelta(minutes=5))
    momentos = {"pedida": pedida, "aprobada": aprobada, "cancelada": None}

    clase = Clase(
        estudiante_id=alumno["usuario"].id,
        profesor_id=profe["usuario"].id,
        materia_id=materia_id,
        etapa_id=etapa_id,
        tema=azar.choice(TEMAS_POR_MATERIA[materia]),
        inicio=p["inicio"],
        duracion_min=p["duracion"],
        fin=p["fin"],
        modalidad=modalidad,
        ubicacion=ubicacion,
        estado=p["estado"],
        creado_el=pedida,
        # El MISMO calculo que cotiza el checkout: hay una sola cuenta de
        # plata en todo el sistema (clases.logica.desglosar).
        **importes_congelados(desglosar(precio_hora, p["duracion"], traslado, comision, iva)),
    )
    if p["estado"] == EstadoClase.cancelada:
        hasta = min(p["inicio"], ahora)
        cancelada = aprobada + (hasta - aprobada) * azar.uniform(0.3, 0.9)
        momentos["cancelada"] = cancelada
        clase.cancelada_por = azar.choice([Actor.estudiante, Actor.estudiante, Actor.profesor])
        clase.motivo = azar.choice(MOTIVOS_CANCELACION)
        clase.actualizado_el = cancelada
    elif p["estado"] != EstadoClase.pendiente:
        clase.actualizado_el = aprobada
    return clase, momentos


def _cobro_de(clase: Clase, tarjeta: Tarjeta, momentos: dict, azar: random.Random) -> Cobro:
    """El cobro de una clase, con los timestamps de cada transicion por la que paso.

      pendiente                    retenido
      aprobada, dictada, no vino   cobrado (al aprobarse)
      cancelada                    reembolsado si ya estaba aprobada,
                                   liberado si todavia era una solicitud
    """
    cobro = Cobro(
        clase_id=clase.id,
        tarjeta_id=tarjeta.id,
        importe=clase.total,
        estado=EstadoCobro.retenido,
        retenido_el=momentos["pedida"],
        creado_el=momentos["pedida"],
    )
    if clase.estado in (EstadoClase.aprobada, EstadoClase.dictada, EstadoClase.no_asistida):
        cobro.estado = EstadoCobro.cobrado
        cobro.cobrado_el = momentos["aprobada"]
    elif clase.estado == EstadoClase.cancelada:
        if azar.random() < 0.7:
            cobro.estado = EstadoCobro.reembolsado
            cobro.cobrado_el = momentos["aprobada"]
            # El reembolso corre en segundo plano, unos segundos despues.
            cobro.reembolsado_el = momentos["cancelada"] + timedelta(seconds=azar.randint(2, 20))
        else:
            cobro.estado = EstadoCobro.liberado
            cobro.liberado_el = momentos["cancelada"]
    return cobro


def _cobro_rechazado(profe: dict, alumno: dict, comision: Decimal, iva: Decimal, ahora: datetime,
                     azar: random.Random) -> Cobro:
    """Una solicitud que el profesor rechazo: la clase se borro y el cobro quedo liberado.

    Por eso clase_id va en NULL (ver la migracion 6d0c95b67436). En el
    historial del alumno sale como "Solicitud rechazada".
    """
    perfil = profe["perfil"]
    precio = perfil.precio_hora_presencial or perfil.precio_hora_online
    total = desglosar(precio, azar.choice(profe["duraciones"]), Decimal("0"), comision, iva)["total"]
    pedida = ahora - timedelta(days=azar.randint(3, SEMANAS_DE_HISTORIA * 7), hours=azar.randint(0, 12))
    return Cobro(
        clase_id=None,
        tarjeta_id=alumno["tarjeta"].id,
        importe=total,
        estado=EstadoCobro.liberado,
        retenido_el=pedida,
        liberado_el=min(pedida + timedelta(hours=azar.randint(1, 30)), ahora),
        creado_el=pedida,
    )


# ===========================================================================
# Auxiliares: lo que se escriben
# ===========================================================================

def _charla(par: dict, nombres: dict, ahora: datetime, azar: random.Random) -> list[tuple]:
    """La conversacion de un alumno y un profesor que tuvieron clase.

    Devuelve [(autor_id, texto, cuando)] en cualquier orden: el que llama la
    ordena y descarta lo que caeria en el futuro.
    """
    alumno, profe = par["alumno"], par["profe"]
    a_id, p_id = alumno["usuario"].id, profe["usuario"].id
    a_nombre, p_nombre = alumno["usuario"].nombre, profe["usuario"].nombre
    clases = sorted(par["clases"], key=lambda c: c.inicio)
    primera = clases[0]
    materia = nombres["materias"][primera.materia_id]
    etapa = _etapa_en_texto(nombres["etapas"].get(primera.etapa_id, "liceo"))
    mensajes = []

    # 1. La consulta antes de reservar, y el aviso de que ya reservo.
    t = primera.creado_el - timedelta(hours=azar.randint(12, 48))
    mensajes.append((a_id, f"¡Hola {p_nombre}! ¿Das clases de {materia} para {etapa}? {azar.choice(CONTEXTOS)}", t))
    t += timedelta(minutes=azar.randint(40, 300))
    mensajes.append((p_id, f"¡Hola {a_nombre}! Sí, claro. ¿Qué temas están viendo?", t))
    t += timedelta(minutes=azar.randint(5, 90))
    mensajes.append((a_id, f"Ahora estamos con {_minuscula(primera.tema)}.", t))
    t += timedelta(minutes=azar.randint(10, 120))
    mensajes.append((p_id, azar.choice(RESPUESTAS_PRIMERA), t))
    mensajes.append((a_id, f"Listo, te mandé la solicitud para el {_cuando(primera.inicio)}. ¡Gracias!",
                     primera.creado_el + timedelta(minutes=azar.randint(1, 15))))

    # 2. Donde es la clase, el dia antes de una que se dio o esta por darse.
    confirmadas = [c for c in clases if c.estado in (EstadoClase.aprobada, EstadoClase.dictada)]
    if confirmadas and azar.random() < 0.6:
        c = azar.choice(confirmadas)
        t = c.inicio - timedelta(hours=azar.randint(14, 30))
        if c.modalidad == Modalidad.online:
            mensajes.append((a_id, f"¿Me pasás el enlace para la clase del {_cuando(c.inicio)}?", t))
            mensajes.append((p_id, "Está en el detalle de la clase, es el mismo de siempre.",
                             t + timedelta(minutes=azar.randint(10, 120))))
        elif c.ubicacion:
            mensajes.append((a_id, f"¿La clase del {_cuando(c.inicio)} es en {c.ubicacion}?", t))
            mensajes.append((p_id, "Sí, ahí te espero. Si llegás antes, avisame.",
                             t + timedelta(minutes=azar.randint(10, 120))))

    # 3. Despues de la ultima clase dictada.
    dictadas = [c for c in clases if c.estado == EstadoClase.dictada]
    if dictadas:
        d = dictadas[-1]
        t = d.fin + timedelta(minutes=azar.randint(30, 300))
        mensajes.append((p_id, azar.choice(DESPUES_DE_CLASE).format(alumno=a_nombre, tema=_minuscula(d.tema)), t))
        mensajes.append((a_id, azar.choice(RESPUESTAS_ALUMNO), t + timedelta(minutes=azar.randint(20, 300))))

    # 4. El aviso de una cancelacion, de quien cancelo.
    canceladas = [c for c in clases if c.estado == EstadoClase.cancelada and c.actualizado_el]
    if canceladas:
        c = canceladas[-1]
        t = c.actualizado_el + timedelta(minutes=1)
        if c.cancelada_por == Actor.estudiante:
            mensajes.append((a_id, f"Perdón, tuve que cancelar la clase del {_cuando(c.inicio)}. {c.motivo}", t))
            mensajes.append((p_id, "No hay problema, cuando quieras reservamos otra.",
                             t + timedelta(minutes=azar.randint(15, 240))))
        else:
            mensajes.append((p_id, f"{a_nombre}, tuve que cancelar la del {_cuando(c.inicio)}, perdón. "
                                   "Ya te devolvieron el pago.", t))
            mensajes.append((a_id, "Tranqui, reservo otro día.", t + timedelta(minutes=azar.randint(15, 240))))

    # 5. Lo que viene: la pregunta por la proxima clase.
    proximas = [c for c in clases if c.inicio > ahora and c.estado in (EstadoClase.aprobada, EstadoClase.pendiente)]
    if proximas:
        c = proximas[0]
        if c.estado == EstadoClase.pendiente:
            t = c.creado_el + timedelta(minutes=azar.randint(5, 40))
            mensajes.append((a_id, f"Hola {p_nombre}, te mandé una solicitud para el {_cuando(c.inicio)}. "
                                   "¿Te viene bien?", t))
        else:
            t = max(ahora - timedelta(hours=azar.randint(1, 40)), c.creado_el + timedelta(hours=1))
            mensajes.append((a_id, f"¿Sigue en pie la clase del {_cuando(c.inicio)}?", t))
            mensajes.append((p_id, f"¡Sí! Te espero a las {c.inicio:%H:%M}.",
                             t + timedelta(minutes=azar.randint(10, 180))))
            # El recordatorio del profesor, el dia antes. Si la clase es en
            # mas de un dia, todavia no se mando (cae en el futuro y se descarta).
            mensajes.append((p_id, f"¡Hola {a_nombre}! Te recuerdo la clase de mañana a las "
                                   f"{c.inicio:%H:%M}. Traé las dudas que tengas.",
                             c.inicio - timedelta(hours=azar.randint(20, 26))))
    return mensajes


def _consulta(alumno: dict, profe: dict, ahora: datetime, azar: random.Random) -> list[tuple]:
    """Un alumno que pregunta antes de reservar. A veces todavia no le contestaron."""
    a_id, p_id = alumno["usuario"].id, profe["usuario"].id
    t = ahora - timedelta(days=azar.randint(0, 20), hours=azar.randint(0, 20), minutes=azar.randint(0, 59))
    mensajes = [(a_id, f"¡Hola {profe['usuario'].nombre}! Vi tu perfil. ¿Tenés lugar para "
                       f"{azar.choice(profe['materias_nombres'])} los {DIAS[azar.randint(0, 4)]}?", t)]
    if azar.random() < 0.7:
        mensajes.append((p_id, "¡Hola! Sí, fijate en mi agenda los horarios libres y reservá cuando quieras.",
                         t + timedelta(minutes=azar.randint(30, 600))))
    return mensajes


# ===========================================================================
# Auxiliares chicos
# ===========================================================================

def _dia_semana(dia: date) -> int:
    """El dia de la semana como lo guarda franja_disponibilidad: 0 = domingo ... 6 = sabado.

    weekday() de Python va de 0 = lunes a 6 = domingo; la tabla sigue a
    Date.getDay() de JavaScript.
    """
    return (dia.weekday() + 1) % 7


def _dia_habil(hoy: date, dias: int) -> date:
    """hoy + dias, corrido al dia habil mas cercano en la misma direccion."""
    dia = hoy + timedelta(days=dias)
    paso = timedelta(days=1 if dias > 0 else -1)
    while dia.weekday() >= 5:  # 5 = sabado, 6 = domingo (aca es datetime, no Date.getDay)
        dia += paso
    return dia


def _se_pisa(inicio: datetime, fin: datetime, intervalos: list) -> bool:
    """True si [inicio, fin) se superpone con alguno de los intervalos."""
    return any(inicio < f and i < fin for i, f in intervalos)


def _cuando(momento: datetime) -> str:
    """"martes 21 a las 18:00", para escribirlo en un mensaje."""
    return f"{DIAS[momento.weekday()]} {momento.day} a las {momento:%H:%M}"


def _minuscula(tema: str | None) -> str:
    """"Leyes de Newton" -> "leyes de Newton" (solo la primera letra)."""
    if not tema:
        return "lo que estamos viendo"
    return tema[0].lower() + tema[1:]


def _etapa_en_texto(etapa: str) -> str:
    """"Bachillerato" -> "bachillerato" para ir en una frase; "UTU" queda igual."""
    return etapa if etapa == UTU else etapa.lower()


def _cerca(lugar, azar: random.Random) -> tuple[Decimal, Decimal]:
    """Un punto a unas cuadras del centroide de un barrio, para que en el mapa
    no queden todos encimados."""
    def mover(valor: Decimal) -> Decimal:
        corrimiento = Decimal(str(round(azar.uniform(-0.004, 0.004), 6)))
        return (valor + corrimiento).quantize(Decimal("0.000001"))

    return mover(lugar.latitud), mover(lugar.longitud)


def _edad(nacimiento: date, hoy: date) -> int:
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def _precio(valor: int | None) -> Decimal | None:
    return Decimal(valor) if valor is not None else None


def _documento(n: int) -> str:
    """Una cedula inventada con formato uruguayo (el digito no verifica)."""
    numero = f"{4_100_000 + n * 7919:,}".replace(",", ".")
    return f"{numero}-{n % 10}"


def _telefono(n: int) -> str:
    return f"09{n % 9 + 1} {n * 37 % 1000:03d} {n * 53 % 1000:03d}"


def _resumen(db) -> None:
    """Imprime cuanto quedo cargado, tabla por tabla."""
    consultas = {
        "usuarios": "SELECT count(*) FROM usuario",
        "  fichas publicadas": "SELECT count(*) FROM perfil_profesor WHERE estado_ficha = 'publicada'",
        "clases": "SELECT count(*) FROM clase",
        "  dictadas / aprobadas / pendientes": (
            "SELECT count(*) FILTER (WHERE estado = 'dictada') || ' / ' || "
            "count(*) FILTER (WHERE estado = 'aprobada') || ' / ' || "
            "count(*) FILTER (WHERE estado = 'pendiente') FROM clase"
        ),
        "  canceladas / no asistidas": (
            "SELECT count(*) FILTER (WHERE estado = 'cancelada') || ' / ' || "
            "count(*) FILTER (WHERE estado = 'no_asistida') FROM clase"
        ),
        "cobros (con los rechazados)": "SELECT count(*) FROM cobro",
        "tarjetas": "SELECT count(*) FROM tarjeta",
        "resenas": "SELECT count(*) FROM resena",
        "hilos": "SELECT count(*) FROM hilo",
        "mensajes / sin leer": (
            "SELECT count(*) || ' / ' || count(*) FILTER (WHERE leido_el IS NULL) FROM mensaje"
        ),
        "franjas / bloqueos": (
            "SELECT (SELECT count(*) FROM franja_disponibilidad) || ' / ' || (SELECT count(*) FROM bloqueo)"
        ),
    }
    for nombre, consulta in consultas.items():
        print(f"  {nombre:36} {db.execute(text(consulta)).scalar()}")


def main() -> None:
    """Corre todo el sembrado en una sola transaccion."""
    db = SesionLocal()
    try:
        limpiar(db)
        catalogos = sembrar_catalogos(db)
        usuarios = sembrar_usuarios(db, catalogos)
        sembrar_agenda(db, usuarios)
        pares = sembrar_clases(db, usuarios, catalogos)
        sembrar_resenas(db, pares)
        sembrar_mensajes(db, pares, usuarios, catalogos)
        db.commit()
        print("Datos de prueba cargados.")
        _resumen(db)
        print(f"  Profesores: profe1 a profe{len(PROFESORES)}@example.com")
        print(f"  Alumnos:    alumno1 a alumno{len(usuarios['estudiantes'])}@example.com")
        print(f"  Clave de todos: {CLAVE_DE_PRUEBA}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
