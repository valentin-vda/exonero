"""Rutas HTTP del modulo perfiles - dueno P1.

Dos grupos:
  /api/perfiles/*   edicion del perfil propio (1e y 1j)
  /api/profesores/* lectura de la ficha publica (1a, 1b, 1c, 1f, 1g, 1h)

La edicion del profesor esta partida en un PUT por seccion del formulario de
1j. Es a proposito: cada seccion se guarda sola, sin mandar la ficha entera y
sin pisar lo que otra pestania dejo a medio editar.
"""

from fastapi import APIRouter, Query, status

from app.dependencias import Db, Yo
from app.modulos.perfiles import esquemas

router_perfiles = APIRouter(prefix="/perfiles", tags=["perfiles"])
router_profesores = APIRouter(prefix="/profesores", tags=["perfiles"])


# ============================================================================
# Perfil del estudiante - 1e
# ============================================================================

@router_perfiles.get("/estudiante/yo", response_model=esquemas.PerfilEstudianteOut)
def obtener_perfil_estudiante(yo: Yo, db: Db):
    """Datos educativos y direccion del alumno del token.

    TODO (P1): implementar. 403 si el rol no es estudiante.
    """
    raise NotImplementedError("P1 - perfiles: GET /perfiles/estudiante/yo")


@router_perfiles.put("/estudiante/yo", response_model=esquemas.PerfilEstudianteOut)
def guardar_perfil_estudiante(datos: esquemas.PerfilEstudianteIn, yo: Yo, db: Db):
    """Guarda etapa, nivel, centro, barrio, direccion y adulto responsable.

    TODO (P1): implementar.
      1. Validar los ids de catalogo con catalogos.logica.existe().
      2. Si cuentas.logica.es_menor(db, yo.id) y falta adulto_nombre o
         adulto_telefono -> ErrorAPI(400, "adulto_responsable_requerido").
      3. Guardar y devolver el perfil actualizado.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/estudiante/yo")


# ============================================================================
# Perfil del profesor - 1j. Un PUT por seccion del formulario.
# ============================================================================

@router_perfiles.get("/profesor/yo", response_model=esquemas.FichaProfesorOut)
def obtener_perfil_profesor(yo: Yo, db: Db):
    """La ficha propia completa, para cargar el formulario de 1j.

    Devuelve lo mismo que GET /profesores/{id} pero sin exigir que este
    publicada: el profesor tiene que poder editar su borrador.

    TODO (P1): implementar. 403 si el rol no es profesor.
    """
    raise NotImplementedError("P1 - perfiles: GET /perfiles/profesor/yo")


@router_perfiles.patch("/profesor/yo/personal", response_model=esquemas.OkOut)
def guardar_personal(datos: esquemas.PersonalProfesorIn, yo: Yo, db: Db):
    """Titulo habilitante y anios de experiencia.

    Los datos de la persona (nombre, telefono, documento) NO van aca: van por
    PATCH /usuarios/yo, que es el mismo endpoint que usa 1e.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 - perfiles: PATCH /perfiles/profesor/yo/personal")


@router_perfiles.put("/profesor/yo/oferta", response_model=esquemas.OkOut)
def guardar_oferta(datos: esquemas.OfertaIn, yo: Yo, db: Db):
    """Materias, etapas con su programa, e idiomas.

    No dispara nada mas: la busqueda consulta profesor_materia directamente, no
    hay indice que reconstruir.

    TODO (P1): implementar.
      1. Validar que los ids existan en los catalogos.
      2. Borrar las filas actuales de profesor_materia, profesor_etapa y
         profesor_idioma de este perfil y volver a insertarlas. Reemplazo
         completo, no diff: es mas simple y mas predecible.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/oferta")


@router_perfiles.put("/profesor/yo/modalidad", response_model=esquemas.OkOut)
def guardar_modalidad(datos: esquemas.ModalidadIn, yo: Yo, db: Db):
    """Modalidad, lugar de clase, direccion del espacio y zonas de traslado.

    La direccion del espacio es parte de la ficha publica: se muestra en 1f.

    TODO (P1): implementar. zonas_traslado se reemplaza entero, igual que la oferta.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/modalidad")


@router_perfiles.put("/profesor/yo/precios", response_model=esquemas.OkOut)
def guardar_precios(datos: esquemas.PreciosIn, yo: Yo, db: Db):
    """Precio por hora presencial y online.

    TODO (P1): implementar. Las clases ya creadas NO se tocan: congelaron su
    precio al crearse.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/precios")


@router_perfiles.put("/profesor/yo/reglas", response_model=esquemas.OkOut)
def guardar_reglas(datos: esquemas.ReglasIn, yo: Yo, db: Db):
    """Duracion minima y maxima, duraciones ofrecidas, descanso, tope diario y
    aviso minimo. Las usa agenda para calcular los huecos libres de 1f.

    TODO (P1): implementar. Las duraciones se guardan en profesor_duracion,
    reemplazando las filas actuales.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/reglas")


@router_perfiles.put("/profesor/yo/bio", response_model=esquemas.OkOut)
def guardar_bio(datos: esquemas.BioIn, yo: Yo, db: Db):
    """Titular, biografia de hasta 600 caracteres y puntos de metodo.

    TODO (P1): implementar. Los puntos van a punto_metodo con su orden.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/bio")


@router_perfiles.post("/profesor/yo/fotos", status_code=status.HTTP_201_CREATED)
def agregar_foto(datos: esquemas.FotoLugarIn, yo: Yo, db: Db):
    """Agrega una foto del lugar. Las muestra 1f.

    TODO (P1): implementar. Si es_portada viene en true, sacarle la portada a
    las demas: solo una puede serlo.
    """
    raise NotImplementedError("P1 - perfiles: POST /perfiles/profesor/yo/fotos")


@router_perfiles.put("/profesor/yo/fotos/{foto_id}", response_model=esquemas.OkOut)
def editar_foto(foto_id: int, datos: esquemas.FotoLugarIn, yo: Yo, db: Db):
    """Cambia epigrafe, orden o portada de una foto ya subida.

    TODO (P1): implementar. 403 si la foto no es de este profesor.
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/fotos/{id}")


@router_perfiles.delete("/profesor/yo/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_foto(foto_id: int, yo: Yo, db: Db):
    """Borra una foto del lugar.

    TODO (P1): implementar. 403 si la foto no es de este profesor.
    """
    raise NotImplementedError("P1 - perfiles: DELETE /perfiles/profesor/yo/fotos/{id}")


@router_perfiles.put("/profesor/yo/estado", response_model=esquemas.OkOut)
def cambiar_estado_ficha(datos: esquemas.EstadoFichaIn, yo: Yo, db: Db):
    """Publicar o pausar la ficha. SOLO las publicadas aparecen en la busqueda.

    TODO (P1): implementar.
      1. Validar que sea borrador, publicada o pausada.
      2. Antes de publicar, exigir el minimo para que la ficha sirva: al menos
         una materia, un precio y una franja de disponibilidad. Si falta algo
         -> ErrorAPI(400, "ficha_incompleta").
    """
    raise NotImplementedError("P1 - perfiles: PUT /perfiles/profesor/yo/estado")


# ============================================================================
# Ficha publica - la leen seis pantallas
# ============================================================================

@router_profesores.get("/resumen", response_model=list[esquemas.ResumenProfesorOut])
def resumen_profesores(db: Db, ids: str = Query(..., description="ids separados por coma")):
    """Version liviana en lote: 1a, 1b, 1c, 1h.

    OJO con el orden: esta ruta va ANTES que /{profesor_id}, o FastAPI
    interpreta "resumen" como un id y devuelve 422.

    TODO (P1): implementar. Parsear ids y llamar a logica.ficha_resumida().
    """
    raise NotImplementedError("P1 - perfiles: GET /profesores/resumen")


@router_profesores.get("/{profesor_id}", response_model=esquemas.FichaProfesorOut)
def ficha_profesor(profesor_id: int, db: Db):
    """La ficha publica completa. EL ENDPOINT MAS COMPARTIDO: 1a, 1b, 1c, 1f, 1g, 1h.

    profesor_id es el id del USUARIO, no el del perfil.

    TODO (P1): implementar.
      1. Buscar el perfil del profesor por usuario_id -> 404 si no existe.
      2. Si la ficha no esta publicada y el que mira no es su dueno -> 404.
         404 y no 403: no hace falta confirmar que la cuenta existe.
      3. Armar FichaProfesorOut con materias, etapas, idiomas, zonas,
         duraciones, puntos de metodo y fotos, resolviendo los nombres de los
         catalogos.
    """
    raise NotImplementedError("P1 - perfiles: GET /profesores/{id}")
