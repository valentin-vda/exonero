"""Datos de prueba. Se corre con:  python -m app.seeds

Va APARTE de las migraciones a proposito: las migraciones cambian la forma de
las tablas, los datos de ejemplo se pueden volver a cargar cuantas veces haga
falta. Si estuvieran mezclados, resetear los datos obligaria a bajar y volver
a subir el esquema.

Tiene que ser IDEMPOTENTE: correrlo dos veces no puede duplicar nada. Por eso
arranca vaciando todas las tablas (ver limpiar) y vuelve a cargar todo.

QUE CARGA (segun la spec):
  - los barrios de Montevideo con su centroide
  - las materias del mockup
  - las etapas educativas
  - unos cuantos centros educativos
  - los idiomas
  - la comision de servicio y la tasa de IVA
  - veinte usuarios de ejemplo, con sus perfiles, disponibilidad y clases
  - unos bloqueos de agenda (P3), para que 1i y 1f muestren alguno
  - una foto de ejemplo del lugar de clase de profe1

Todos los usuarios entran con la clave "exonero123":
  profe1@example.com ... profe8@example.com     (profe7 en borrador, profe8 pausada)
  alumno1@example.com ... alumno12@example.com

Por que example.com: es un dominio reservado para ejemplos (RFC 2606), no es
de nadie. Un dominio .test seria lo mas natural, pero el validador de correos
del backend (EmailStr) lo rechaza por ser de "uso especial", y con esos
usuarios no se podria hacer login.

Las fechas de las clases se calculan desde HOY, asi siempre hay clases
proximas y pasadas sin importar cuando se corra.

QUE NO CARGA (todavia): mensajes ni resenas.
"""

import base64
import random
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
    LugarClase,
    Modalidad,
    Rol,
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

CLAVE_DE_PRUEBA = "exonero123"
ZONA = ZoneInfo(ajustes.ZONA_HORARIA)
FOTO_AULA = Path(__file__).with_name("datos") / "aula-ejemplo.jpg"

# Semilla fija: las coordenadas "al azar" salen iguales en todas las maquinas.
SEMILLA = 2026

# ---------------------------------------------------------------------------
# Listas de referencia. Estas son datos reales y se pueden usar tal cual.
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
]

IDIOMAS = ["Español", "Inglés", "Portugués"]

# Comision de la plataforma e IVA. En tabla y no como constante para poder
# cambiarlos sin recompilar. El IVA uruguayo basico es 22 %.
PARAMETROS = [
    ("comision_servicio", 10.0),
    ("tasa_iva", 22.0),
]

# ---------------------------------------------------------------------------
# Usuarios de ejemplo. Personas inventadas.
# ---------------------------------------------------------------------------

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
]

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

# Para el adulto responsable de los menores (ver usuario.fecha_nacimiento).
ADULTOS = ["Ana", "Carlos", "Laura", "Jorge", "Patricia", "Fernando"]

CALLES = ["Av. 18 de Julio", "Bulevar Artigas", "Av. Italia", "Canelones", "Colonia", "Av. Brasil"]

METODO = [
    "Arrancamos por lo que mas te cuesta, no por el orden del programa.",
    "En cada clase hacemos ejercicios de examenes anteriores.",
    "Te llevas un resumen escrito de lo que vimos.",
    "Dejo una practica corta para la semana siguiente.",
]

TEMAS = [
    "Repaso para el parcial",
    "Ejercicios del practico",
    "Dudas del teorico",
    "Preparar el examen de diciembre",
]

MOTIVOS_CANCELACION = [
    "Me surgio un parcial ese dia.",
    "Estoy enfermo, lo pasamos para otra semana.",
    "Tuve un imprevisto familiar.",
]

# Las clases que se le crean a cada profesor con ficha publicada.
# Las horas caen dentro de las franjas de sembrar_agenda (de lunes a viernes,
# desde las 15 hasta pasadas las 18:30).
PLAN_CLASES = [
    # (estado, dias desde hoy, hora de inicio, duracion en minutos)
    (EstadoClase.dictada, -14, 15, 60),
    (EstadoClase.dictada, -7, 17, 90),
    (EstadoClase.cancelada, -3, 15, 60),
    (EstadoClase.aprobada, 2, 17, 90),
    (EstadoClase.pendiente, 4, 15, 60),
]

# El estado del cobro que acompana a cada estado de la clase (ver pagos/modelos.py).
COBRO_SEGUN_CLASE = {
    EstadoClase.pendiente: EstadoCobro.retenido,
    EstadoClase.aprobada: EstadoCobro.cobrado,
    EstadoClase.dictada: EstadoCobro.cobrado,
    EstadoClase.cancelada: EstadoCobro.reembolsado,
}


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

    # Vigentes desde antes de la clase mas vieja de los seeds, para que las ya
    # dictadas tambien tengan parametros que les correspondan.
    parametros = {clave: Decimal(str(valor)) for clave, valor in PARAMETROS}
    db.add_all(
        ParametroPlataforma(clave=clave, valor=valor, vigente_desde=date(2025, 1, 1))
        for clave, valor in parametros.items()
    )
    db.flush()

    return {
        "barrios": barrios,
        "materias": materias,
        "etapas": etapas,
        "centros": centros,
        "idiomas": idiomas,
        "comision": parametros["comision_servicio"],
        "iva": parametros["tasa_iva"],
    }


def sembrar_usuarios(db, catalogos: dict) -> dict:
    """Crea los veinte usuarios de ejemplo: ocho profesores y doce alumnos.

    Los profesores van primero, asi profe1..profe8 tienen los ids 1 a 8.
    Seis de los ocho tienen la ficha publicada; si no, la busqueda de 1c sale
    casi vacia.
    """
    hoy = datetime.now(ZONA).date()
    # Hasheada UNA sola vez: bcrypt es lento a proposito, y veinte hashes
    # harian que el seed tarde varios segundos.
    hash_clave = hashear_clave(CLAVE_DE_PRUEBA)
    azar = random.Random(SEMILLA + 1)
    barrios = catalogos["barrios"]

    profesores = []
    for n, datos in enumerate(PROFESORES, start=1):
        usuario = Usuario(
            correo=f"profe{n}@example.com",
            hash_clave=hash_clave,
            nombre=datos["nombre"],
            apellido=datos["apellido"],
            documento=_documento(n),
            telefono=_telefono(n),
            fecha_nacimiento=date(1978 + 2 * n, n, 10 + n),
            rol=Rol.profesor,
        )
        db.add(usuario)
        db.flush()  # el perfil necesita usuario.id

        barrio = barrios[datos["barrio"]]
        latitud, longitud = _cerca(barrio, azar)
        a_domicilio = datos["lugar"] in (LugarClase.a_domicilio, LugarClase.ambos)
        duracion_max = datos.get("duracion_max", 120)
        perfil = PerfilProfesor(
            usuario_id=usuario.id,
            titular=datos["titular"],
            biografia=(
                f"Doy clases particulares hace {datos['anios']} anios. "
                f"{datos['titulo']}. Me adapto al ritmo de cada alumno y "
                "trabajo con el material que usan en clase."
            ),
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
        )
        db.add(perfil)
        db.flush()  # las siete tablas de la oferta necesitan perfil.id

        materias = [catalogos["materias"][m].id for m in datos["materias"]]
        etapas = [catalogos["etapas"][e].id for e in datos["etapas"]]
        db.add_all(ProfesorMateria(perfil_profesor_id=perfil.id, materia_id=m) for m in materias)
        db.add_all(
            ProfesorEtapa(
                perfil_profesor_id=perfil.id,
                etapa_id=catalogos["etapas"][e].id,
                programa="Plan 2006 y reformulacion 2023" if e in ("Ciclo básico", "Bachillerato") else None,
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
            db.add_all(
                ProfesorZona(perfil_profesor_id=perfil.id, barrio_id=barrios[z].id) for z in zonas
            )
        db.add_all(
            ProfesorDuracion(perfil_profesor_id=perfil.id, minutos=m)
            for m in (60, 90, 120)
            if m <= duracion_max
        )
        db.add_all(
            PuntoMetodo(perfil_profesor_id=perfil.id, texto=METODO[(n + k) % len(METODO)], orden=k)
            for k in range(3)
        )
        if n == 1:
            imagen = base64.b64encode(FOTO_AULA.read_bytes()).decode("ascii")
            db.add(
                FotoLugar(
                    perfil_profesor_id=perfil.id,
                    imagen_base64=f"data:image/jpeg;base64,{imagen}",
                    epigrafe="Espacio de clase",
                    orden=0,
                    es_portada=True,
                )
            )
        profesores.append(
            {"usuario": usuario, "perfil": perfil, "materias": materias, "etapas": etapas}
        )

    estudiantes = []
    for n, (nombre, apellido, nacimiento, etapa, nivel, centro, barrio) in enumerate(
        ESTUDIANTES, start=1
    ):
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
        # La tarjeta de prueba de siempre. NUNCA una real (ver pagos/modelos.py).
        tarjeta = Tarjeta(
            usuario_id=usuario.id,
            numero="4111111111111111",
            titular=f"{nombre} {apellido}".upper(),
            vence_mes=12,
            vence_anio=hoy.year + 3,
            ccv="123",
        )
        db.add_all([perfil, tarjeta])
        estudiantes.append({"usuario": usuario, "perfil": perfil, "tarjeta": tarjeta})

    db.flush()
    return {"profesores": profesores, "estudiantes": estudiantes}


def sembrar_agenda(db, usuarios: dict) -> None:
    """Carga franjas de disponibilidad para cada profesor.

    Sin franjas, el calendario de 1f sale vacio y no se puede reservar nada.
    Todos atienden de lunes a viernes (unos de 14 a 20 y otros de 15 a 21), y
    la mitad tambien los sabados de manana.
    """
    for n, profe in enumerate(usuarios["profesores"]):
        perfil = profe["perfil"]
        desde = 14 if n % 2 == 0 else 15
        # dia_semana: 0 = domingo ... 6 = sabado, como Date.getDay().
        franjas = [(dia, time(desde), time(desde + 6)) for dia in range(1, 6)]
        if n % 2 == 0:
            franjas.append((6, time(9), time(13)))
        db.add_all(
            FranjaDisponibilidad(
                perfil_profesor_id=perfil.id,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                modalidad=perfil.modalidad,
            )
            for dia, inicio, fin in franjas
        )
    db.flush()


# Los bloqueos de ejemplo: (profesor, dias desde hoy, desde, hasta, motivo).
# Caen despues de la ultima clase de PLAN_CLASES (la pendiente, a 4 a 6 dias),
# asi ninguno pisa una aprobada, que es justo lo que agenda no deja hacer.
PLAN_BLOQUEOS = [
    (0, 8, time(14), time(16), "Turno medico"),
    (1, 9, time(15), time(21), "Mesa de examen en el liceo"),
    (2, 10, time(0), time(23, 59), "Congreso de docentes"),
]


def sembrar_bloqueos(db, usuarios: dict) -> None:
    """Carga unos bloqueos de agenda para profe1, profe2 y profe3.

    Sin bloqueos, la pestana de 1i sale vacia y el calendario de 1f nunca
    muestra un dia tapado.
    """
    hoy = datetime.now(ZONA).date()
    for n, dias, desde, hasta, motivo in PLAN_BLOQUEOS:
        dia = _dia_habil(hoy, dias)
        db.add(Bloqueo(
            perfil_profesor_id=usuarios["profesores"][n]["perfil"].id,
            inicio=datetime.combine(dia, desde, ZONA),
            fin=datetime.combine(dia, hasta, ZONA),
            motivo=motivo,
        ))
    db.flush()


def sembrar_clases(db, usuarios: dict, catalogos: dict) -> None:
    """Crea clases de ejemplo en los distintos estados, cada una con su cobro.

    A cada profesor con ficha publicada le toca PLAN_CLASES: pendientes para
    1i, aprobadas para la proxima clase de 1a y 1b, dictadas para el historial
    de 1b y las metricas de 1d, y canceladas para la tasa de cancelacion.

    Hay una sola aprobada por profesor, asi que la restriccion EXCLUDE (que
    impide dos aprobadas encimadas) no salta.
    """
    ahora = datetime.now(ZONA)
    estudiantes = usuarios["estudiantes"]
    publicados = [
        p for p in usuarios["profesores"] if p["perfil"].estado_ficha == EstadoFicha.publicada
    ]

    n = 0
    for i, profe in enumerate(publicados):
        perfil = profe["perfil"]
        for estado, dias, hora, duracion in PLAN_CLASES:
            alumno = estudiantes[n % len(estudiantes)]
            n += 1
            # i % 3 corre un poco las fechas para que no caigan todas el mismo dia.
            inicio = datetime.combine(_dia_habil(ahora.date(), dias + i % 3), time(hora), ZONA)

            if perfil.modalidad == Modalidad.ambas:
                modalidad = Modalidad.presencial if n % 2 else Modalidad.online
            else:
                modalidad = perfil.modalidad
            if modalidad == Modalidad.presencial:
                precio_hora = perfil.precio_hora_presencial
                a_domicilio = perfil.lugar_clase == LugarClase.a_domicilio
                traslado = perfil.costo_traslado if a_domicilio else Decimal("0")
                ubicacion = alumno["perfil"].direccion if a_domicilio else perfil.direccion_espacio
            else:
                precio_hora = perfil.precio_hora_online
                traslado = Decimal("0")
                ubicacion = f"https://meet.exonero.test/clase-{n}"

            # La solicitud se hizo unos dias antes de la clase, nunca en el futuro.
            creada_el = min(inicio - timedelta(days=3), ahora - timedelta(hours=2))
            clase = Clase(
                estudiante_id=alumno["usuario"].id,
                profesor_id=profe["usuario"].id,
                materia_id=profe["materias"][n % len(profe["materias"])],
                etapa_id=profe["etapas"][n % len(profe["etapas"])],
                tema=TEMAS[n % len(TEMAS)],
                inicio=inicio,
                duracion_min=duracion,
                fin=inicio + timedelta(minutes=duracion),
                modalidad=modalidad,
                ubicacion=ubicacion,
                estado=estado,
                creado_el=creada_el,
                # El MISMO calculo que cotiza el checkout: hay una sola cuenta
                # de plata en todo el sistema (clases.logica.desglosar).
                **importes_congelados(
                    desglosar(precio_hora, duracion, traslado, catalogos["comision"], catalogos["iva"])
                ),
            )
            if estado == EstadoClase.cancelada:
                clase.cancelada_por = Actor.estudiante if n % 2 else Actor.profesor
                clase.motivo = MOTIVOS_CANCELACION[n % len(MOTIVOS_CANCELACION)]
            if estado == EstadoClase.dictada:
                perfil.clases_dictadas += 1
            db.add(clase)
            db.flush()  # el cobro necesita clase.id
            db.add(_cobro(clase, alumno["tarjeta"], creada_el, ahora))

    db.flush()


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _cobro(clase: Clase, tarjeta: Tarjeta, retenido_el: datetime, ahora: datetime) -> Cobro:
    """El cobro de una clase, con los timestamps de cada transicion por la que paso."""
    estado = COBRO_SEGUN_CLASE[clase.estado]
    cobro = Cobro(
        clase_id=clase.id,
        tarjeta_id=tarjeta.id,
        importe=clase.total,
        estado=estado,
        retenido_el=retenido_el,
        creado_el=retenido_el,
    )
    if estado in (EstadoCobro.cobrado, EstadoCobro.reembolsado):
        # El profesor aprueba unas horas despues de la solicitud.
        cobro.cobrado_el = min(retenido_el + timedelta(hours=5), ahora)
    if estado == EstadoCobro.reembolsado:
        cobro.reembolsado_el = clase.inicio - timedelta(days=1)
    return cobro


def _dia_habil(hoy: date, dias: int) -> date:
    """hoy + dias, corrido al dia habil mas cercano en la misma direccion.

    Las clases de los seeds caen de lunes a viernes, que es cuando todos los
    profesores tienen franjas.
    """
    dia = hoy + timedelta(days=dias)
    paso = timedelta(days=1 if dias > 0 else -1)
    while dia.weekday() >= 5:  # 5 = sabado, 6 = domingo (aca es datetime, no Date.getDay)
        dia += paso
    return dia


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


def main() -> None:
    """Corre todo el sembrado en una sola transaccion."""
    db = SesionLocal()
    try:
        limpiar(db)
        catalogos = sembrar_catalogos(db)
        usuarios = sembrar_usuarios(db, catalogos)
        sembrar_agenda(db, usuarios)
        sembrar_clases(db, usuarios, catalogos)
        sembrar_bloqueos(db, usuarios)
        db.commit()
        print("Datos de prueba cargados.")
        print(f"  Profesores: profe1 a profe{len(PROFESORES)}@example.com")
        print(f"  Alumnos:    alumno1 a alumno{len(ESTUDIANTES)}@example.com")
        print(f"  Clave de todos: {CLAVE_DE_PRUEBA}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
