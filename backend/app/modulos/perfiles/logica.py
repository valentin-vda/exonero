"""Funciones publicas del modulo perfiles - dueno P1.

perfiles sirve la ficha publica. Es el modulo que mas consultan los demas.

Quien consume que:
  - cuentas  -> crear_perfil_estudiante(), crear_perfil_profesor() en el registro
  - cuentas  -> cabecera_estudiante() para GET /usuarios/yo
  - cuentas  -> pausar_ficha() cuando un profesor se da de baja
  - busqueda -> ficha_resumida() para armar resultados
  - agenda   -> perfil_profesor_de() y reglas_profesor() para los huecos libres
  - clases   -> precio_vigente(), reglas_profesor() y condiciones_de_reserva()
                para cotizar; direccion_estudiante() para la ubicacion;
                ficha_resumida() y cabeceras_estudiantes() para la contraparte;
                sumar_clase_dictada() al marcar una clase como dictada
  - resenas  -> escribir_puntaje() al recalcular el promedio

Como en cuentas: estas funciones validan y guardan, pero NO hacen commit. El
commit lo hace la ruta (ver la explicacion al principio de cuentas/logica.py).

LOS DOS IDS DEL PROFESOR. Un profesor tiene dos numeros:
  usuario.id          la persona. Lo usan las clases, los hilos, las resenas
                      y las URLs (/profesores/12 es el usuario 12).
  perfil_profesor.id  su ficha. De este cuelgan las siete tablas de la oferta
                      (materias, etapas, idiomas, zonas, duraciones, puntos de
                      metodo y fotos) y las de agenda.
perfil_profesor_de() es el puente: recibe el usuario.id y devuelve el perfil.
"""

from decimal import Decimal

from sqlalchemy import column, delete, func, select, table, update
from sqlalchemy.orm import Session

from app.enums import EstadoFicha, LugarClase, Modalidad, Rol
from app.errores import ErrorAPI, no_es_tuyo, no_existe
from app.modulos.cuentas import logica as cuentas
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

# Tope de fotos del lugar: son los cuatro espacios que dibuja el mockup de 1j.
MAX_FOTOS = 4


# ---------------------------------------------------------------------------
# Los catalogos, vistos "de lejos"
# ---------------------------------------------------------------------------
#
# La ficha muestra NOMBRES ("Matematica", "Cordon"), pero en las tablas de
# perfiles solo hay ids. Los nombres estan en las tablas de catalogos (P2).
#
# La regla del proyecto es no importar catalogos/modelos.py. Por eso aca se
# describen esas tablas a mano, con solo las dos columnas que hacen falta, y
# por su NOMBRE de tabla: igual que las claves foraneas, ForeignKey("barrio.id").
# Solo se usan para LEER. Nada de perfiles escribe en un catalogo.
_CATALOGOS = {
    "materia": table("materia", column("id"), column("nombre")),
    "etapa_educativa": table("etapa_educativa", column("id"), column("nombre")),
    "idioma": table("idioma", column("id"), column("nombre")),
    "barrio": table("barrio", column("id"), column("nombre")),
    "centro_educativo": table("centro_educativo", column("id"), column("nombre")),
}


def _nombres(db: Session, catalogo: str, ids) -> dict[int, str]:
    """{id: nombre} para esos ids del catalogo, en UNA sola consulta.

    Ejemplo: _nombres(db, "materia", [1, 2]) -> {1: "Matematica", 2: "Fisica"}
    Los ids que no existen simplemente no aparecen en el resultado.
    """
    ids = {i for i in ids if i is not None}
    if not ids:
        return {}
    t = _CATALOGOS[catalogo]
    filas = db.execute(select(t.c.id, t.c.nombre).where(t.c.id.in_(ids)))
    return {fila.id: fila.nombre for fila in filas}


def _nombre(db: Session, catalogo: str, id_: int | None) -> str | None:
    """El nombre de UN id, o None. Atajo de _nombres para un solo valor."""
    return _nombres(db, catalogo, [id_]).get(id_)


def _validar_catalogo(db: Session, catalogo: str, ids) -> None:
    """400 si alguno de esos ids no existe en el catalogo.

    Ejemplo de error: "materia_no_existe". Asi el frontend recibe un codigo
    claro en vez del 500 que daria la clave foranea al hacer el commit.
    """
    pedidos = {i for i in ids if i is not None}
    if pedidos - set(_nombres(db, catalogo, pedidos)):
        raise ErrorAPI(400, f"{catalogo}_no_existe")


# ---------------------------------------------------------------------------
# Alta, la llama cuentas en el registro
# ---------------------------------------------------------------------------

def crear_perfil_estudiante(db: Session, usuario_id: int) -> PerfilEstudiante:
    """Crea un perfil_estudiante vacio para un usuario recien registrado.

    Vacio a proposito: el alumno completa etapa, centro y direccion despues,
    desde 1e. Sin esta fila, GET /usuarios/yo no tiene de donde sacar la
    cabecera de 1a.
    """
    perfil = PerfilEstudiante(usuario_id=usuario_id)
    db.add(perfil)
    db.flush()
    return perfil


def crear_perfil_profesor(db: Session, usuario_id: int) -> PerfilProfesor:
    """Crea un perfil_profesor en estado borrador.

    Borrador quiere decir que NO aparece en la busqueda. Se publica desde 1j
    cuando el profesor completo materias y precios.
    """
    perfil = PerfilProfesor(usuario_id=usuario_id, estado_ficha=EstadoFicha.borrador)
    db.add(perfil)
    db.flush()
    return perfil


# ---------------------------------------------------------------------------
# Lectura, la llaman los otros modulos
# ---------------------------------------------------------------------------

def perfil_estudiante_de(db: Session, usuario_id: int) -> PerfilEstudiante | None:
    """El PerfilEstudiante de un usuario, o None."""
    return db.scalar(select(PerfilEstudiante).where(PerfilEstudiante.usuario_id == usuario_id))


def perfil_profesor_de(db: Session, usuario_id: int) -> PerfilProfesor | None:
    """Devuelve el PerfilProfesor de un usuario, o None.

    OJO con los dos ids (ver arriba): recibe usuario.id, no perfil_profesor.id.
    """
    return db.scalar(select(PerfilProfesor).where(PerfilProfesor.usuario_id == usuario_id))


def cabecera_estudiante(db: Session, usuario_id: int) -> dict | None:
    """Etapa, nivel, centro, barrio y puntaje del alumno, con los nombres ya resueltos.

    Es el bloque "estudiante" de GET /usuarios/yo, o sea el subtitulo de 1a y
    de 1e: "5.o de Bachillerato - Liceo Bauza - Cordon".

    Devuelve None si el usuario no es estudiante.
    """
    perfil = perfil_estudiante_de(db, usuario_id)
    if perfil is None:
        return None
    return {
        "etapa": _nombre(db, "etapa_educativa", perfil.etapa_id),
        "nivel": perfil.nivel,
        "centro": _nombre(db, "centro_educativo", perfil.centro_id),
        "barrio": _nombre(db, "barrio", perfil.barrio_id),
        "puntaje_promedio": float(perfil.puntaje_promedio),
        "cantidad_resenas": perfil.cantidad_resenas,
    }


def reglas_profesor(db: Session, perfil_profesor_id: int) -> dict:
    """Las reglas con las que agenda calcula los huecos libres.

    Devuelve duracion_min, duracion_max, duraciones ofrecidas, descanso_min,
    max_clases_dia y aviso_minimo_horas.

    OJO: recibe el id del PERFIL (agenda trabaja con perfil_profesor.id).
    """
    perfil = db.get(PerfilProfesor, perfil_profesor_id)
    if perfil is None:
        raise no_existe("perfil")
    return {
        "duracion_min": perfil.duracion_min,
        "duracion_max": perfil.duracion_max,
        "duraciones": _duraciones(db, perfil.id),
        "descanso_min": perfil.descanso_min,
        "max_clases_dia": perfil.max_clases_dia,
        "aviso_minimo_horas": perfil.aviso_minimo_horas,
    }


def precio_vigente(db: Session, usuario_profesor_id: int, modalidad: str) -> Decimal | None:
    """El precio por hora actual del profesor para esa modalidad, o None.

    Lo llama clases al cotizar. Es el precio de HOY: la clase lo congela al
    crearse, y de ahi en mas no cambia aunque el profesor lo suba.

    None quiere decir "no ofrece esa modalidad" (clases responde sin_precio).
    """
    perfil = perfil_profesor_de(db, usuario_profesor_id)
    if perfil is None:
        return None
    if Modalidad(modalidad) == Modalidad.presencial:
        return perfil.precio_hora_presencial
    return perfil.precio_hora_online


def ficha_resumida(db: Session, ids_usuario: list[int]) -> list[dict]:
    """Version liviana de varios profesores, con pocas consultas.

    Es lo que devuelve GET /profesores/resumen?ids=1,2,3, y lo que usa busqueda
    para armar las filas de resultados sin pedir la ficha completa de cada uno.

    Evita el problema "N+1": en vez de una consulta por profesor (que con 30
    resultados serian 30+ consultas), hace cuatro en total, sin importar
    cuantos profesores se pidan. Devuelve la lista EN EL MISMO ORDEN de
    ids_usuario, porque busqueda ya los ordeno por relevancia.
    """
    if not ids_usuario:
        return []

    # 1. Los perfiles de esos usuarios.
    perfiles = db.scalars(
        select(PerfilProfesor).where(PerfilProfesor.usuario_id.in_(ids_usuario))
    ).all()
    por_usuario = {p.usuario_id: p for p in perfiles}

    # 2. Nombre, apellido y foto, de cuentas.
    personas = cuentas.datos_basicos_varios(db, list(por_usuario))

    # 3. Las materias de todos esos perfiles juntas: (perfil_id, materia_id).
    filas = db.execute(
        select(ProfesorMateria.perfil_profesor_id, ProfesorMateria.materia_id)
        .where(ProfesorMateria.perfil_profesor_id.in_([p.id for p in perfiles]))
        .order_by(ProfesorMateria.id)
    ).all()
    # 4. Los nombres de esas materias.
    nombres = _nombres(db, "materia", [f.materia_id for f in filas])
    materias_de: dict[int, list[str]] = {}
    for fila in filas:
        materias_de.setdefault(fila.perfil_profesor_id, []).append(nombres.get(fila.materia_id, ""))

    resultado = []
    for usuario_id in ids_usuario:
        perfil = por_usuario.get(usuario_id)
        if perfil is None:
            continue  # ese id no es un profesor: se saltea en silencio
        persona = personas[usuario_id]
        precios = [p for p in (perfil.precio_hora_presencial, perfil.precio_hora_online) if p is not None]
        resultado.append({
            "id": usuario_id,
            "nombre": persona["nombre"],
            "apellido": persona["apellido"],
            "foto_base64": persona["foto_base64"],
            "materias": materias_de.get(perfil.id, []),
            "precio_hora": min(precios) if precios else None,
            "puntaje_promedio": perfil.puntaje_promedio,
            "cantidad_resenas": perfil.cantidad_resenas,
        })
    return resultado


def escribir_puntaje(db: Session, usuario_id: int, promedio: Decimal, cantidad: int) -> None:
    """Guarda el puntaje desnormalizado en el perfil que corresponda.

    Es la UNICA puerta por la que se escriben puntaje_promedio y
    cantidad_resenas, y solo la llama el modulo resenas. Si alguien mas los
    escribe, los numeros dejan de coincidir con la tabla de resenas.

    Sirve para los dos perfiles: mira el rol del usuario y actualiza el correcto.
    """
    usuario = cuentas.obtener_usuario(db, usuario_id)
    if usuario is None:
        raise no_existe("usuario")
    if usuario.rol == Rol.profesor:
        perfil = perfil_profesor_de(db, usuario_id)
    else:
        perfil = perfil_estudiante_de(db, usuario_id)
    perfil.puntaje_promedio = promedio
    perfil.cantidad_resenas = cantidad
    db.flush()


# ---------------------------------------------------------------------------
# Lo que pide clases (P4): reservar, mostrar la contraparte, contar dictadas.
# Se agregaron con P4; ninguna de las de arriba cambio.
# ---------------------------------------------------------------------------

def condiciones_de_reserva(db: Session, usuario_profesor_id: int) -> dict | None:
    """Lo que clases necesita del profesor para cotizar y crear una clase.

    El precio sale de precio_vigente() y las duraciones de reglas_profesor();
    esto es el resto. Devuelve None si el usuario no es profesor.

      perfil_id          para llamar a reglas_profesor() (ojo: los dos ids)
      publicada          solo se le puede reservar a una ficha publicada
      modalidad          presencial, online o ambas
      lugar_clase        espacio_propio, a_domicilio, ambos o espacio_publico
      hace_traslado      True si va a la casa del alumno (a_domicilio o ambos)
      costo_traslado     lo que cobra por ir
      direccion_espacio  donde da la clase cuando no se traslada
    """
    perfil = perfil_profesor_de(db, usuario_profesor_id)
    if perfil is None:
        return None
    return {
        "perfil_id": perfil.id,
        "publicada": perfil.estado_ficha == EstadoFicha.publicada,
        "modalidad": perfil.modalidad.value,
        "lugar_clase": perfil.lugar_clase.value,
        "hace_traslado": perfil.lugar_clase in (LugarClase.a_domicilio, LugarClase.ambos),
        "costo_traslado": perfil.costo_traslado,
        "direccion_espacio": perfil.direccion_espacio,
    }


def direccion_estudiante(db: Session, usuario_id: int) -> str | None:
    """La direccion del alumno, o None. Es donde va el profesor cuando se traslada.

    clases la copia en la clase al crearla (clase.ubicacion).
    """
    perfil = perfil_estudiante_de(db, usuario_id)
    return perfil.direccion if perfil else None


def cabeceras_estudiantes(db: Session, ids_usuario: list[int]) -> dict[int, dict]:
    """Lo mismo que cabecera_estudiante() pero para varios alumnos, en lote.

    Devuelve {usuario_id: {etapa, nivel, centro, barrio, puntaje_promedio,
    cantidad_resenas}}; los ids que no son alumnos no aparecen. Lo usa clases
    para la contraparte de cada fila cuando mira el profesor (el panel 1d
    muestra "Bachillerato - Liceo Bauza" debajo del nombre del alumno). Con
    cabecera_estudiante() en un for serian cuatro consultas por fila; asi son
    cuatro en total, como ficha_resumida().
    """
    if not ids_usuario:
        return {}
    perfiles = db.scalars(
        select(PerfilEstudiante).where(PerfilEstudiante.usuario_id.in_(ids_usuario))
    ).all()
    etapas = _nombres(db, "etapa_educativa", [p.etapa_id for p in perfiles])
    centros = _nombres(db, "centro_educativo", [p.centro_id for p in perfiles])
    barrios = _nombres(db, "barrio", [p.barrio_id for p in perfiles])
    return {
        p.usuario_id: {
            "etapa": etapas.get(p.etapa_id),
            "nivel": p.nivel,
            "centro": centros.get(p.centro_id),
            "barrio": barrios.get(p.barrio_id),
            "puntaje_promedio": p.puntaje_promedio,
            "cantidad_resenas": p.cantidad_resenas,
        }
        for p in perfiles
    }


def sumar_clase_dictada(db: Session, usuario_profesor_id: int) -> None:
    """Suma uno a clases_dictadas del profesor. La llama clases al marcar una
    clase como dictada.

    Es la unica puerta por la que cambia ese contador (lo muestra la ficha
    publica). Va con un UPDATE ... SET x = x + 1 y no leyendo y escribiendo
    desde Python: si dos clases se marcan a la vez, ninguna de las dos sumas
    se pierde.
    """
    resultado = db.execute(
        update(PerfilProfesor)
        .where(PerfilProfesor.usuario_id == usuario_profesor_id)
        .values(clases_dictadas=PerfilProfesor.clases_dictadas + 1)
    )
    if resultado.rowcount == 0:
        raise no_existe("perfil")
    db.flush()


# ---------------------------------------------------------------------------
# Perfil del estudiante - 1e
# ---------------------------------------------------------------------------

def guardar_perfil_estudiante(db: Session, usuario_id: int, datos) -> PerfilEstudiante:
    """Guarda etapa, nivel, centro, barrio, direccion y adulto responsable.

    `datos` es un PerfilEstudianteIn. PUT: se reemplazan todos los campos.
    """
    perfil = perfil_estudiante_de(db, usuario_id)

    # 1. Los ids tienen que existir en los catalogos.
    _validar_catalogo(db, "etapa_educativa", [datos.etapa_id])
    _validar_catalogo(db, "centro_educativo", [datos.centro_id])
    _validar_catalogo(db, "barrio", [datos.barrio_id])

    # 2. Si es menor de edad, el adulto responsable es obligatorio. La edad sale
    #    de usuario.fecha_nacimiento, que es de cuentas: por eso el frontend
    #    guarda primero los datos personales (PATCH /usuarios/yo) y despues esto.
    adulto_nombre = _limpio(datos.adulto_nombre)
    adulto_telefono = _limpio(datos.adulto_telefono)
    if cuentas.es_menor(db, usuario_id) and not (adulto_nombre and adulto_telefono):
        raise ErrorAPI(400, "adulto_responsable_requerido")

    # 3. Guardar.
    perfil.etapa_id = datos.etapa_id
    perfil.nivel = _limpio(datos.nivel)
    perfil.centro_id = datos.centro_id
    perfil.barrio_id = datos.barrio_id
    perfil.direccion = _limpio(datos.direccion)
    perfil.latitud = datos.latitud
    perfil.longitud = datos.longitud
    perfil.adulto_nombre = adulto_nombre
    perfil.adulto_telefono = adulto_telefono
    db.flush()
    return perfil


# ---------------------------------------------------------------------------
# La ficha del profesor - la leen GET /profesores/{id} y 1j
# ---------------------------------------------------------------------------

def ficha_completa(db: Session, usuario_id: int) -> dict | None:
    """Todo lo de un profesor en un diccionario, o None si no es profesor.

    Trae lo publico Y lo privado. Quien filtra es la ruta, con el esquema de
    respuesta (ver MiFichaOut en esquemas.py):
      GET /profesores/{id}      -> FichaProfesorOut descarta lo privado
      GET /perfiles/profesor/yo -> MiFichaOut lo deja todo
    """
    perfil = perfil_profesor_de(db, usuario_id)
    if perfil is None:
        return None
    persona = cuentas.datos_basicos(db, usuario_id)
    pid = perfil.id

    # --- Las siete tablas de la oferta, una consulta cada una -------------
    materia_ids = db.scalars(
        select(ProfesorMateria.materia_id)
        .where(ProfesorMateria.perfil_profesor_id == pid)
        .order_by(ProfesorMateria.id)
    ).all()
    etapas = db.scalars(
        select(ProfesorEtapa).where(ProfesorEtapa.perfil_profesor_id == pid).order_by(ProfesorEtapa.id)
    ).all()
    idioma_ids = db.scalars(
        select(ProfesorIdioma.idioma_id)
        .where(ProfesorIdioma.perfil_profesor_id == pid)
        .order_by(ProfesorIdioma.id)
    ).all()
    zona_ids = db.scalars(
        select(ProfesorZona.barrio_id).where(ProfesorZona.perfil_profesor_id == pid).order_by(ProfesorZona.id)
    ).all()
    puntos = db.scalars(
        select(PuntoMetodo.texto).where(PuntoMetodo.perfil_profesor_id == pid).order_by(PuntoMetodo.orden)
    ).all()
    fotos = db.scalars(
        select(FotoLugar).where(FotoLugar.perfil_profesor_id == pid).order_by(FotoLugar.orden, FotoLugar.id)
    ).all()

    # --- Los nombres de los catalogos, una consulta por catalogo ------------
    materias = _nombres(db, "materia", materia_ids)
    etapas_n = _nombres(db, "etapa_educativa", [e.etapa_id for e in etapas])
    idiomas = _nombres(db, "idioma", idioma_ids)
    barrios = _nombres(db, "barrio", [*zona_ids, perfil.barrio_id])

    return {
        # --- Publico (FichaProfesorOut) ---
        "id": usuario_id,
        "nombre": persona["nombre"],
        "apellido": persona["apellido"],
        "foto_base64": persona["foto_base64"],
        "titular": perfil.titular,
        "biografia": perfil.biografia,
        "puntos_metodo": list(puntos),
        "titulo_habilitante": perfil.titulo_habilitante,
        "anios_experiencia": perfil.anios_experiencia,
        "materias": [{"id": m, "nombre": materias.get(m, "")} for m in materia_ids],
        "etapas": [
            {"id": e.etapa_id, "nombre": etapas_n.get(e.etapa_id), "programa": e.programa}
            for e in etapas
        ],
        "idiomas": [idiomas[i] for i in idioma_ids if i in idiomas],
        "modalidad": perfil.modalidad.value,
        "lugar_clase": perfil.lugar_clase.value,
        "barrio": barrios.get(perfil.barrio_id),
        "direccion_espacio": perfil.direccion_espacio,
        "latitud": perfil.latitud,
        "longitud": perfil.longitud,
        "zonas_traslado": [barrios[z] for z in zona_ids if z in barrios],
        "costo_traslado": perfil.costo_traslado,
        "precio_hora_presencial": perfil.precio_hora_presencial,
        "precio_hora_online": perfil.precio_hora_online,
        "duraciones": _duraciones(db, pid),
        "aviso_minimo_horas": perfil.aviso_minimo_horas,
        "fotos": [
            {"id": f.id, "imagen_base64": f.imagen_base64, "epigrafe": f.epigrafe, "es_portada": f.es_portada}
            for f in fotos
        ],
        "puntaje_promedio": perfil.puntaje_promedio,
        "cantidad_resenas": perfil.cantidad_resenas,
        "clases_dictadas": perfil.clases_dictadas,
        # --- Privado (solo MiFichaOut) ---
        "barrio_id": perfil.barrio_id,
        "idioma_ids": list(idioma_ids),
        "zona_ids": list(zona_ids),
        "duracion_min": perfil.duracion_min,
        "duracion_max": perfil.duracion_max,
        "descanso_min": perfil.descanso_min,
        "max_clases_dia": perfil.max_clases_dia,
        "formato": perfil.formato.value,
        "cupo_min": perfil.cupo_min,
        "cupo_max": perfil.cupo_max,
        "estado_ficha": perfil.estado_ficha.value,
    }


# ---------------------------------------------------------------------------
# Edicion de la ficha - 1j. Una funcion por seccion del formulario.
# Todas reciben el PerfilProfesor ya resuelto (lo busca la ruta).
# ---------------------------------------------------------------------------

def guardar_personal(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Titulo habilitante, anios de experiencia y barrio base.

    PATCH: `cambios` tiene solo lo que vino en el JSON.
    """
    cambios = datos.model_dump(exclude_unset=True)
    if "barrio_id" in cambios:
        _validar_catalogo(db, "barrio", [cambios["barrio_id"]])
    if "titulo_habilitante" in cambios:
        cambios["titulo_habilitante"] = _limpio(cambios["titulo_habilitante"])
    # setattr(perfil, "anios_experiencia", 6) es lo mismo que
    # perfil.anios_experiencia = 6, pero con el nombre del campo en una variable.
    for campo, valor in cambios.items():
        setattr(perfil, campo, valor)
    db.flush()


def guardar_oferta(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Materias, etapas con su programa, e idiomas. Reemplazo completo."""
    # dict.fromkeys saca los repetidos sin cambiar el orden: [3, 1, 3] -> [3, 1].
    materias = list(dict.fromkeys(datos.materias))
    idiomas = list(dict.fromkeys(datos.idiomas))
    etapas = list({e.id: e for e in datos.etapas}.values())

    _validar_catalogo(db, "materia", materias)
    _validar_catalogo(db, "idioma", idiomas)
    _validar_catalogo(db, "etapa_educativa", [e.id for e in etapas])

    _reemplazar_filas(db, ProfesorMateria, perfil.id, [
        ProfesorMateria(perfil_profesor_id=perfil.id, materia_id=m) for m in materias
    ])
    _reemplazar_filas(db, ProfesorEtapa, perfil.id, [
        ProfesorEtapa(perfil_profesor_id=perfil.id, etapa_id=e.id, programa=_limpio(e.programa))
        for e in etapas
    ])
    _reemplazar_filas(db, ProfesorIdioma, perfil.id, [
        ProfesorIdioma(perfil_profesor_id=perfil.id, idioma_id=i) for i in idiomas
    ])
    db.flush()


def guardar_modalidad(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Modalidad, lugar de clase, direccion del espacio y zonas de traslado."""
    zonas = list(dict.fromkeys(datos.zonas_traslado))
    _validar_catalogo(db, "barrio", zonas)

    perfil.modalidad = datos.modalidad
    perfil.lugar_clase = datos.lugar_clase
    perfil.direccion_espacio = _limpio(datos.direccion_espacio)
    perfil.costo_traslado = datos.costo_traslado
    _reemplazar_filas(db, ProfesorZona, perfil.id, [
        ProfesorZona(perfil_profesor_id=perfil.id, barrio_id=b) for b in zonas
    ])
    db.flush()


def guardar_precios(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Precio por hora presencial y online.

    Las clases ya creadas NO se tocan: congelaron su precio al crearse.
    """
    perfil.precio_hora_presencial = datos.precio_hora_presencial
    perfil.precio_hora_online = datos.precio_hora_online
    db.flush()


def guardar_reglas(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Duraciones, descanso, tope diario, aviso minimo, formato y cupos."""
    if datos.duracion_max < datos.duracion_min:
        raise ErrorAPI(400, "duraciones_incoherentes")

    # Las duraciones ofrecidas tienen que caer entre la minima y la maxima.
    duraciones = sorted(set(datos.duraciones))
    if any(d < datos.duracion_min or d > datos.duracion_max for d in duraciones):
        raise ErrorAPI(400, "duracion_fuera_de_rango")
    # Sin ninguna, el alumno no podria reservar nada: se ofrece al menos la minima.
    if not duraciones:
        duraciones = [datos.duracion_min]

    if datos.cupo_min and datos.cupo_max and datos.cupo_min > datos.cupo_max:
        raise ErrorAPI(400, "cupos_incoherentes")

    perfil.duracion_min = datos.duracion_min
    perfil.duracion_max = datos.duracion_max
    perfil.descanso_min = datos.descanso_min
    perfil.max_clases_dia = datos.max_clases_dia
    perfil.aviso_minimo_horas = datos.aviso_minimo_horas
    perfil.formato = datos.formato
    perfil.cupo_min = datos.cupo_min
    perfil.cupo_max = datos.cupo_max
    _reemplazar_filas(db, ProfesorDuracion, perfil.id, [
        ProfesorDuracion(perfil_profesor_id=perfil.id, minutos=m) for m in duraciones
    ])
    db.flush()


def guardar_bio(db: Session, perfil: PerfilProfesor, datos) -> None:
    """Titular, biografia de hasta 600 caracteres y puntos de metodo en orden."""
    perfil.titular = _limpio(datos.titular)
    perfil.biografia = _limpio(datos.biografia)
    # Los renglones vacios del formulario se descartan.
    puntos = [p.strip() for p in datos.puntos_metodo if p and p.strip()]
    _reemplazar_filas(db, PuntoMetodo, perfil.id, [
        PuntoMetodo(perfil_profesor_id=perfil.id, texto=texto, orden=orden)
        for orden, texto in enumerate(puntos)
    ])
    db.flush()


# --- Fotos del lugar --------------------------------------------------------

def agregar_foto(db: Session, perfil: PerfilProfesor, datos) -> FotoLugar:
    """Agrega una foto al final. La primera que se sube es la portada."""
    cuentas.validar_imagen_base64(datos.imagen_base64)

    actuales = _fotos_de(db, perfil.id)
    if len(actuales) >= MAX_FOTOS:
        raise ErrorAPI(409, "maximo_fotos")

    es_portada = datos.es_portada or not actuales
    if es_portada:
        _sacar_portada(actuales)

    foto = FotoLugar(
        perfil_profesor_id=perfil.id,
        imagen_base64=datos.imagen_base64,
        epigrafe=_limpio(datos.epigrafe),
        orden=len(actuales),  # va al final de la lista
        es_portada=es_portada,
    )
    db.add(foto)
    db.flush()  # para tener foto.id y devolverlo
    return foto


def editar_foto(db: Session, perfil: PerfilProfesor, foto_id: int, datos) -> None:
    """Cambia epigrafe, orden o portada de una foto ya subida."""
    foto = _foto_propia(db, perfil, foto_id)
    if datos.es_portada and not foto.es_portada:
        _sacar_portada(_fotos_de(db, perfil.id))  # solo una puede ser portada
        foto.es_portada = True
    foto.epigrafe = _limpio(datos.epigrafe)
    foto.orden = datos.orden
    db.flush()


def borrar_foto(db: Session, perfil: PerfilProfesor, foto_id: int) -> None:
    """Borra una foto. Si era la portada, la portada pasa a la primera que queda."""
    foto = _foto_propia(db, perfil, foto_id)
    era_portada = foto.es_portada
    db.delete(foto)
    db.flush()
    if era_portada:
        quedan = _fotos_de(db, perfil.id)
        if quedan:
            quedan[0].es_portada = True
            db.flush()


# --- Publicar o pausar --------------------------------------------------------

def cambiar_estado_ficha(db: Session, perfil: PerfilProfesor, estado: EstadoFicha) -> None:
    """Borrador, publicada o pausada. SOLO las publicadas aparecen en la busqueda.

    Antes de publicar se exige lo minimo para que la ficha sirva:
      - al menos una materia
      - precio para cada modalidad que ofrece (sin precio no se puede cotizar)

    La spec pide ademas al menos una franja de disponibilidad. Las franjas son
    del modulo agenda (P3) y perfiles no puede leer sus tablas. Cuando agenda
    tenga una funcion publica para saberlo (por ejemplo tiene_franjas()), el
    chequeo va aca, junto a los otros dos.
    """
    if estado == EstadoFicha.publicada:
        cantidad_materias = db.scalar(
            select(func.count())
            .select_from(ProfesorMateria)
            .where(ProfesorMateria.perfil_profesor_id == perfil.id)
        )
        if cantidad_materias == 0 or not _tiene_precios(perfil):
            raise ErrorAPI(400, "ficha_incompleta")
    perfil.estado_ficha = estado
    db.flush()


def pausar_ficha(db: Session, usuario_id: int) -> None:
    """Saca la ficha de la busqueda. La llama cuentas cuando el profesor se da de baja."""
    perfil = perfil_profesor_de(db, usuario_id)
    if perfil is not None and perfil.estado_ficha == EstadoFicha.publicada:
        perfil.estado_ficha = EstadoFicha.pausada
        db.flush()


# ---------------------------------------------------------------------------
# Auxiliares privadas
# ---------------------------------------------------------------------------

def _reemplazar_filas(db: Session, modelo, perfil_id: int, nuevas: list) -> None:
    """Borra todas las filas de `modelo` de este perfil y agrega `nuevas`.

    Es el "reemplazo completo" que usan materias, etapas, idiomas, zonas,
    duraciones y puntos de metodo. Mas simple que calcular que se agrego y que
    se quito: el frontend manda la lista entera y queda exactamente esa.
    """
    db.execute(delete(modelo).where(modelo.perfil_profesor_id == perfil_id))
    db.add_all(nuevas)


def _duraciones(db: Session, perfil_id: int) -> list[int]:
    return list(db.scalars(
        select(ProfesorDuracion.minutos)
        .where(ProfesorDuracion.perfil_profesor_id == perfil_id)
        .order_by(ProfesorDuracion.minutos)
    ))


def _fotos_de(db: Session, perfil_id: int) -> list[FotoLugar]:
    return list(db.scalars(
        select(FotoLugar).where(FotoLugar.perfil_profesor_id == perfil_id).order_by(FotoLugar.orden, FotoLugar.id)
    ))


def _foto_propia(db: Session, perfil: PerfilProfesor, foto_id: int) -> FotoLugar:
    """La foto, si existe (404) y es de este profesor (403)."""
    foto = db.get(FotoLugar, foto_id)
    if foto is None:
        raise no_existe("foto")
    if foto.perfil_profesor_id != perfil.id:
        raise no_es_tuyo()
    return foto


def _sacar_portada(fotos: list[FotoLugar]) -> None:
    for foto in fotos:
        foto.es_portada = False


def _tiene_precios(perfil: PerfilProfesor) -> bool:
    """True si hay precio para cada modalidad que el profesor ofrece."""
    necesita_presencial = perfil.modalidad in (Modalidad.presencial, Modalidad.ambas)
    necesita_online = perfil.modalidad in (Modalidad.online, Modalidad.ambas)
    if necesita_presencial and perfil.precio_hora_presencial is None:
        return False
    if necesita_online and perfil.precio_hora_online is None:
        return False
    return True


def _limpio(texto: str | None) -> str | None:
    """Saca los espacios de los costados. Un texto vacio se guarda como NULL."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None
