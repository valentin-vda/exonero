"""Contratos de entrada y salida del modulo perfiles.

El de salida mas importante es FichaProfesorOut: es GET /profesores/{id}, el
endpoint mas compartido del sistema (1a, 1b, 1c, 1f, 1g y 1h).
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Perfil del estudiante - 1e
# ---------------------------------------------------------------------------

class PerfilEstudianteOut(BaseModel):
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

    El adulto responsable es obligatorio si el usuario es menor de edad; eso se
    valida en logica y no aca, porque depende de usuario.fecha_nacimiento.
    """

    etapa_id: int | None = None
    nivel: str | None = None
    centro_id: int | None = None
    barrio_id: int | None = None
    direccion: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    adulto_nombre: str | None = None
    adulto_telefono: str | None = None


# ---------------------------------------------------------------------------
# Ficha publica del profesor - GET /profesores/{id}
# ---------------------------------------------------------------------------

class MateriaEnFicha(BaseModel):
    id: int
    nombre: str


class EtapaEnFicha(BaseModel):
    id: int
    nombre: str | None = None
    programa: str | None = None


class FotoEnFicha(BaseModel):
    imagen_base64: str
    epigrafe: str | None = None
    es_portada: bool = False


class FichaProfesorOut(BaseModel):
    """GET /profesores/{id} - 1a, 1b, 1c, 1f, 1g, 1h.

    El endpoint mas compartido del sistema. P2 lo consume en el detalle aunque
    1f sea su pantalla: los datos son de perfiles, asi que lo construye P1.
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
    precio_hora: Decimal | None = None
    puntaje_promedio: Decimal = Decimal(0)
    cantidad_resenas: int = 0


# ---------------------------------------------------------------------------
# Edicion de la ficha - 1j. Una seccion del formulario, un PUT.
# ---------------------------------------------------------------------------

class PersonalProfesorIn(BaseModel):
    """PATCH /perfiles/profesor/yo/personal - lo del profesor que no esta en usuario."""

    titulo_habilitante: str | None = None
    anios_experiencia: int | None = None


class OfertaIn(BaseModel):
    """PUT /perfiles/profesor/yo/oferta - materias, etapas e idiomas.

    Reemplaza las tres listas enteras: es mas simple y mas predecible que
    mandar altas y bajas sueltas.
    """

    materias: list[int] = []
    etapas: list[EtapaEnFicha] = []
    idiomas: list[int] = []


class ModalidadIn(BaseModel):
    """PUT /perfiles/profesor/yo/modalidad - donde y como da clase."""

    modalidad: str
    lugar_clase: str
    barrio_id: int | None = None
    direccion_espacio: str | None = None
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    zonas_traslado: list[int] = []
    costo_traslado: Decimal = Decimal(0)


class PreciosIn(BaseModel):
    """PUT /perfiles/profesor/yo/precios.

    No afecta clases ya creadas: cada clase congelo su precio al crearse.
    """

    precio_hora_presencial: Decimal | None = None
    precio_hora_online: Decimal | None = None


class ReglasIn(BaseModel):
    """PUT /perfiles/profesor/yo/reglas - lo que usa agenda para los huecos."""

    duracion_min: int = 60
    duracion_max: int = 120
    duraciones: list[int] = []
    descanso_min: int = 0
    max_clases_dia: int | None = None
    aviso_minimo_horas: int = 12


class BioIn(BaseModel):
    """PUT /perfiles/profesor/yo/bio."""

    titular: str | None = None
    biografia: str | None = Field(default=None, max_length=600)
    puntos_metodo: list[str] = []


class FotoLugarIn(BaseModel):
    """POST y PUT /perfiles/profesor/yo/fotos."""

    imagen_base64: str
    epigrafe: str | None = None
    orden: int = 0
    es_portada: bool = False


class EstadoFichaIn(BaseModel):
    """PUT /perfiles/profesor/yo/estado - borrador, publicada o pausada."""

    estado_ficha: str


class OkOut(BaseModel):
    ok: bool = True
