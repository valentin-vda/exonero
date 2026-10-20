"""Contratos de entrada y salida del modulo perfiles.

El de salida mas importante es FichaProfesorOut: es GET /profesores/{id}, el
endpoint mas compartido del sistema (1a, 1b, 1c, 1f, 1g y 1h).

Recordatorio de Pydantic: cada clase es la forma de un JSON. Las "In" son lo
que manda el frontend (FastAPI las valida antes de entrar a la ruta y
responde 422 si algo no cumple). Las "Out" son lo que se responde.
Field(ge=0) quiere decir "mayor o igual a 0"; le = "menor o igual".
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums import EstadoFicha, Formato, LugarClase, Modalidad


# ---------------------------------------------------------------------------
# Perfil del estudiante - 1e
# ---------------------------------------------------------------------------

class PerfilEstudianteOut(BaseModel):
    # from_attributes: se puede construir directo desde el objeto de la tabla
    # (la ruta devuelve el PerfilEstudiante y Pydantic lee sus atributos).
    model_config = ConfigDict(from_attributes=True)

    etapa_id: int | None = None
    nivel: str | None = None
    centro_id: int | None = None
    barrio_id: int | None = None
    direccion: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    adulto_nombre: str | None = None
    adulto_telefono: str | None = None
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0


class PerfilEstudianteIn(BaseModel):
    """Cuerpo de PUT /perfiles/estudiante/yo.

    PUT reemplaza todo: el frontend manda siempre los nueve campos.

    El adulto responsable es obligatorio si el usuario es menor de edad; eso se
    valida en logica y no aca, porque depende de usuario.fecha_nacimiento.

    latitud/longitud: no hay geocodificacion (pasar una direccion a
    coordenadas). El frontend manda el centroide del barrio elegido.
    """

    etapa_id: int | None = None
    nivel: str | None = Field(default=None, max_length=40)
    centro_id: int | None = None
    barrio_id: int | None = None
    direccion: str | None = Field(default=None, max_length=200)
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    adulto_nombre: str | None = Field(default=None, max_length=120)
    adulto_telefono: str | None = Field(default=None, max_length=30)


# ---------------------------------------------------------------------------
# Ficha publica del profesor - GET /profesores/{id}
# ---------------------------------------------------------------------------

class MateriaEnFicha(BaseModel):
    id: int
    nombre: str


class EtapaEnFicha(BaseModel):
    id: int
    nombre: str | None = None
    programa: str | None = Field(default=None, max_length=120)


class FotoEnFicha(BaseModel):
    id: int  # para editarla o borrarla desde 1j, y como key en las listas de React
    imagen_base64: str
    epigrafe: str | None = None
    es_portada: bool = False


class FichaProfesorOut(BaseModel):
    """GET /profesores/{id} - 1a, 1b, 1c, 1f, 1g, 1h.

    El endpoint mas compartido del sistema. P2 lo consume en el detalle aunque
    1f sea su pantalla: los datos son de perfiles, asi que lo construye P1.

    Trae NOMBRES (para mostrar), no ids. Lo privado del profesor (descanso,
    tope diario, estado de la ficha) no esta aca: esta en MiFichaOut.
    """

    id: int  # id del USUARIO, no del perfil
    nombre: str
    apellido: str
    foto_base64: str | None = None

    titular: str | None = None
    biografia: str | None = None
    puntos_metodo: list[str] = []
    titulo_habilitante: str | None = None
    anios_experiencia: int | None = None

    materias: list[MateriaEnFicha] = []
    etapas: list[EtapaEnFicha] = []
    idiomas: list[str] = []

    modalidad: str
    lugar_clase: str
    barrio: str | None = None
    direccion_espacio: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    zonas_traslado: list[str] = []
    costo_traslado: Decimal = Decimal(0)

    precio_hora_presencial: Decimal | None = None
    precio_hora_online: Decimal | None = None
    duraciones: list[int] = []
    aviso_minimo_horas: int = 12

    fotos: list[FotoEnFicha] = []

    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0
    clases_dictadas: int = 0


class MiFichaOut(FichaProfesorOut):
    """GET /perfiles/profesor/yo - la ficha PROPIA, para llenar el formulario de 1j.

    Hereda todo lo de FichaProfesorOut y agrega:
      - los ids que el formulario necesita para mandar de vuelta (los de la
        ficha publica son nombres, y con un nombre no se puede guardar)
      - las reglas privadas que no se muestran a los alumnos
      - el estado de la ficha (borrador, publicada o pausada)

    logica.ficha_completa() arma UN solo diccionario con todo. Cuando la ruta
    publica lo devuelve con FichaProfesorOut, Pydantic descarta solo los campos
    de mas: asi lo privado nunca sale en GET /profesores/{id}.
    """

    barrio_id: int | None = None
    idioma_ids: list[int] = []
    zona_ids: list[int] = []

    duracion_min: int = 60
    duracion_max: int = 120
    descanso_min: int = 0
    max_clases_dia: int | None = None
    formato: str = "individual"
    cupo_min: int | None = None
    cupo_max: int | None = None

    estado_ficha: str = "borrador"


class ResumenProfesorOut(BaseModel):
    """GET /profesores/resumen?ids=1,2,3 - 1a, 1b, 1c, 1h.

    Version liviana en lote para carruseles y listas. NO trae biografia, fotos
    del lugar ni puntos de metodo: esas listas se recorren muchas veces y la
    foto en base64 pesa.
    """

    id: int
    nombre: str
    apellido: str
    foto_base64: str | None = None
    materias: list[str] = []
    precio_hora: Decimal | None = None  # el mas bajo de los dos: "desde $700"
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0


# ---------------------------------------------------------------------------
# Edicion de la ficha - 1j. Una seccion del formulario, un PUT.
# ---------------------------------------------------------------------------

class PersonalProfesorIn(BaseModel):
    """PATCH /perfiles/profesor/yo/personal - lo del profesor que no esta en usuario.

    Es la parte de "Informacion personal" de 1j que no es de la cuenta: el
    titulo, los anios y el barrio base (con su centroide, para el mapa).
    PATCH: solo se tocan los campos que vienen.
    """

    titulo_habilitante: str | None = Field(default=None, max_length=160)
    anios_experiencia: int | None = Field(default=None, ge=0, le=70)
    barrio_id: int | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None


class OfertaIn(BaseModel):
    """PUT /perfiles/profesor/yo/oferta - materias, etapas e idiomas.

    Reemplaza las tres listas enteras: es mas simple y mas predecible que
    mandar altas y bajas sueltas.
    """

    materias: list[int] = []
    etapas: list[EtapaEnFicha] = []  # de cada etapa se usan id y programa
    idiomas: list[int] = []


class ModalidadIn(BaseModel):
    """PUT /perfiles/profesor/yo/modalidad - donde y como da clase.

    Con los tipos Modalidad y LugarClase (los enums de app/enums.py), FastAPI
    rechaza solo cualquier valor que no este en la lista.
    """

    modalidad: Modalidad
    lugar_clase: LugarClase
    direccion_espacio: str | None = Field(default=None, max_length=200)
    zonas_traslado: list[int] = []  # ids de barrio
    costo_traslado: Decimal = Field(default=Decimal(0), ge=0)


class PreciosIn(BaseModel):
    """PUT /perfiles/profesor/yo/precios.

    No afecta clases ya creadas: cada clase congelo su precio al crearse.
    """

    precio_hora_presencial: Decimal | None = Field(default=None, ge=0)
    precio_hora_online: Decimal | None = Field(default=None, ge=0)


class ReglasIn(BaseModel):
    """PUT /perfiles/profesor/yo/reglas - lo que usa agenda para los huecos.

    Tambien el formato (individual o grupal) y los cupos. Lo grupal esta fuera
    de v1: se guarda para que el formulario de 1j no lo pierda, pero nada lo lee.
    """

    duracion_min: int = Field(default=60, ge=30, le=480)
    duracion_max: int = Field(default=120, ge=30, le=480)
    duraciones: list[int] = []
    descanso_min: int = Field(default=0, ge=0, le=240)
    max_clases_dia: int | None = Field(default=None, ge=1, le=24)
    aviso_minimo_horas: int = Field(default=12, ge=0, le=168)
    formato: Formato = Formato.individual
    cupo_min: int | None = Field(default=None, ge=1, le=50)
    cupo_max: int | None = Field(default=None, ge=1, le=50)


class BioIn(BaseModel):
    """PUT /perfiles/profesor/yo/bio."""

    titular: str | None = Field(default=None, max_length=160)
    biografia: str | None = Field(default=None, max_length=600)
    puntos_metodo: list[str] = []


class FotoLugarIn(BaseModel):
    """POST /perfiles/profesor/yo/fotos - una foto nueva."""

    imagen_base64: str
    epigrafe: str | None = Field(default=None, max_length=120)
    es_portada: bool = False


class EditarFotoIn(BaseModel):
    """PUT /perfiles/profesor/yo/fotos/{id} - cambiar una foto ya subida.

    Sin la imagen: para cambiar el epigrafe no hace falta volver a mandar
    cientos de KB. Para cambiar la imagen en si, se borra y se sube otra.
    """

    epigrafe: str | None = Field(default=None, max_length=120)
    orden: int = Field(default=0, ge=0)
    es_portada: bool = False


class FotoCreadaOut(BaseModel):
    """Respuesta de POST /perfiles/profesor/yo/fotos: el id de la foto nueva."""

    id: int


class EstadoFichaIn(BaseModel):
    """PUT /perfiles/profesor/yo/estado - borrador, publicada o pausada."""

    estado_ficha: EstadoFicha


class OkOut(BaseModel):
    ok: bool = True
