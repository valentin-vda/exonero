"""Rutas HTTP del modulo perfiles - dueno P1.

Dos grupos:
  /api/perfiles/*   edicion del perfil propio (1e y 1j)
  /api/profesores/* lectura de la ficha publica (1a, 1b, 1c, 1f, 1g, 1h)

La edicion del profesor esta partida en un PUT por seccion del formulario de
1j. Es a proposito: cada seccion se guarda sola, sin mandar la ficha entera y
sin pisar lo que otra pestania dejo a medio editar.

Las rutas de /perfiles/estudiante usan `Estudiante` y las de
/perfiles/profesor usan `Profesor` (ver app/dependencias.py): ademas del token,
exigen el rol. Un profesor que llama a /perfiles/estudiante/yo recibe 403.

Igual que en cuentas: cada ruta llama a logica.py, hace el commit y responde.
"""

from fastapi import APIRouter, Query, status

from app.dependencias import Db, Estudiante, Profesor
from app.enums import EstadoFicha
from app.errores import ErrorAPI, no_existe
from app.modulos.perfiles import esquemas, logica

router_perfiles = APIRouter(prefix="/perfiles", tags=["perfiles"])
router_profesores = APIRouter(prefix="/profesores", tags=["perfiles"])

# Lo que devuelven los PUT que no tienen otra cosa que contar.
OK = {"ok": True}


# ============================================================================
# Perfil del estudiante - 1e
# ============================================================================

@router_perfiles.get("/estudiante/yo", response_model=esquemas.PerfilEstudianteOut)
def obtener_perfil_estudiante(yo: Estudiante, db: Db):
    """Datos educativos y direccion del alumno del token."""
    return logica.perfil_estudiante_de(db, yo.id)


@router_perfiles.put("/estudiante/yo", response_model=esquemas.PerfilEstudianteOut)
def guardar_perfil_estudiante(datos: esquemas.PerfilEstudianteIn, yo: Estudiante, db: Db):
    """Guarda etapa, nivel, centro, barrio, direccion y adulto responsable.

    Errores: 400 <catalogo>_no_existe (un id que no esta en el catalogo),
             400 adulto_responsable_requerido (es menor y falta el adulto).
    """
    perfil = logica.guardar_perfil_estudiante(db, yo.id, datos)
    db.commit()
    return perfil


# ============================================================================
# Perfil del profesor - 1j. Un PUT por seccion del formulario.
# ============================================================================

@router_perfiles.get("/profesor/yo", response_model=esquemas.MiFichaOut)
def obtener_perfil_profesor(yo: Profesor, db: Db):
    """La ficha propia completa, para cargar el formulario de 1j.

    Devuelve lo mismo que GET /profesores/{id} mas lo privado (MiFichaOut), y
    sin exigir que este publicada: el profesor tiene que poder editar su
    borrador.
    """
    return logica.ficha_completa(db, yo.id)


@router_perfiles.patch("/profesor/yo/personal", response_model=esquemas.OkOut)
def guardar_personal(datos: esquemas.PersonalProfesorIn, yo: Profesor, db: Db):
    """Titulo habilitante, anios de experiencia y barrio base.

    Los datos de la persona (nombre, telefono, documento) NO van aca: van por
    PATCH /usuarios/yo, que es el mismo endpoint que usa 1e.
    """
    logica.guardar_personal(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.put("/profesor/yo/oferta", response_model=esquemas.OkOut)
def guardar_oferta(datos: esquemas.OfertaIn, yo: Profesor, db: Db):
    """Materias, etapas con su programa, e idiomas. Reemplazo completo.

    No dispara nada mas: la busqueda consulta profesor_materia directamente, no
    hay indice que reconstruir.
    """
    logica.guardar_oferta(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.put("/profesor/yo/modalidad", response_model=esquemas.OkOut)
def guardar_modalidad(datos: esquemas.ModalidadIn, yo: Profesor, db: Db):
    """Modalidad, lugar de clase, direccion del espacio y zonas de traslado.

    La direccion del espacio es parte de la ficha publica: se muestra en 1f.
    """
    logica.guardar_modalidad(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.put("/profesor/yo/precios", response_model=esquemas.OkOut)
def guardar_precios(datos: esquemas.PreciosIn, yo: Profesor, db: Db):
    """Precio por hora presencial y online.

    Las clases ya creadas NO se tocan: congelaron su precio al crearse.
    """
    logica.guardar_precios(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.put("/profesor/yo/reglas", response_model=esquemas.OkOut)
def guardar_reglas(datos: esquemas.ReglasIn, yo: Profesor, db: Db):
    """Duracion minima y maxima, duraciones ofrecidas, descanso, tope diario,
    aviso minimo, formato y cupos. agenda las usa para los huecos libres de 1f.

    Errores: 400 duraciones_incoherentes, 400 duracion_fuera_de_rango,
             400 cupos_incoherentes.
    """
    logica.guardar_reglas(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.put("/profesor/yo/bio", response_model=esquemas.OkOut)
def guardar_bio(datos: esquemas.BioIn, yo: Profesor, db: Db):
    """Titular, biografia de hasta 600 caracteres y puntos de metodo."""
    logica.guardar_bio(db, _mi_perfil(db, yo), datos)
    db.commit()
    return OK


@router_perfiles.post(
    "/profesor/yo/fotos",
    response_model=esquemas.FotoCreadaOut,
    status_code=status.HTTP_201_CREATED,
)
def agregar_foto(datos: esquemas.FotoLugarIn, yo: Profesor, db: Db):
    """Agrega una foto del lugar. Las muestra 1f. Devuelve el id de la foto nueva.

    Errores: 400 foto_invalida, 400 foto_muy_grande, 409 maximo_fotos.
    """
    foto = logica.agregar_foto(db, _mi_perfil(db, yo), datos)
    db.commit()
    return {"id": foto.id}


@router_perfiles.put("/profesor/yo/fotos/{foto_id}", response_model=esquemas.OkOut)
def editar_foto(foto_id: int, datos: esquemas.EditarFotoIn, yo: Profesor, db: Db):
    """Cambia epigrafe, orden o portada de una foto ya subida.

    Errores: 404 foto_no_existe, 403 no_es_tuyo (la foto es de otro profesor).
    """
    logica.editar_foto(db, _mi_perfil(db, yo), foto_id, datos)
    db.commit()
    return OK


@router_perfiles.delete("/profesor/yo/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_foto(foto_id: int, yo: Profesor, db: Db):
    """Borra una foto del lugar.

    Errores: 404 foto_no_existe, 403 no_es_tuyo.
    """
    logica.borrar_foto(db, _mi_perfil(db, yo), foto_id)
    db.commit()
    return None


@router_perfiles.put("/profesor/yo/estado", response_model=esquemas.OkOut)
def cambiar_estado_ficha(datos: esquemas.EstadoFichaIn, yo: Profesor, db: Db):
    """Publicar o pausar la ficha. SOLO las publicadas aparecen en la busqueda.

    Error: 400 ficha_incompleta (para publicar hace falta al menos una materia
    y el precio de cada modalidad que ofrece).
    """
    logica.cambiar_estado_ficha(db, _mi_perfil(db, yo), datos.estado_ficha)
    db.commit()
    return OK


# ============================================================================
# Ficha publica - la leen seis pantallas. No piden token.
# ============================================================================

@router_profesores.get("/resumen", response_model=list[esquemas.ResumenProfesorOut])
def resumen_profesores(db: Db, ids: str = Query(..., description="ids separados por coma")):
    """Version liviana en lote: 1a, 1b, 1c, 1h. Ejemplo: /profesores/resumen?ids=1,4,6

    OJO con el orden: esta ruta va ANTES que /{profesor_id}, o FastAPI
    interpreta "resumen" como un id y devuelve 422.
    """
    try:
        lista = [int(parte) for parte in ids.split(",") if parte.strip()]
    except ValueError:
        raise ErrorAPI(400, "ids_invalidos")
    # Tope para que nadie pida diez mil fichas de una.
    return logica.ficha_resumida(db, lista[:50])


@router_profesores.get("/{profesor_id}", response_model=esquemas.FichaProfesorOut)
def ficha_profesor(profesor_id: int, db: Db):
    """La ficha publica completa. EL ENDPOINT MAS COMPARTIDO: 1a, 1b, 1c, 1f, 1g, 1h.

    profesor_id es el id del USUARIO, no el del perfil.

    Si no existe o no esta publicada, 404 (y no 403): no hace falta confirmar
    que la cuenta existe. El propio profesor ve su borrador por
    GET /perfiles/profesor/yo.

    response_model=FichaProfesorOut descarta los campos privados que trae
    ficha_completa() (ver MiFichaOut en esquemas.py).
    """
    ficha = logica.ficha_completa(db, profesor_id)
    if ficha is None or ficha["estado_ficha"] != EstadoFicha.publicada.value:
        raise no_existe("profesor")
    return ficha


# ============================================================================
# Auxiliares
# ============================================================================

def _mi_perfil(db, yo):
    """El perfil del profesor del token. Siempre existe: lo crea el registro."""
    perfil = logica.perfil_profesor_de(db, yo.id)
    if perfil is None:
        raise no_existe("perfil")
    return perfil
