"""Tablas del modulo perfiles - dueno P1.

Nueve tablas: los dos perfiles y las siete que cuelgan del perfil del profesor
(su oferta). perfiles es quien sirve la ficha publica que consumen 1a, 1b, 1c,
1f, 1g y 1h.

Las FK a catalogos (materia, etapa, barrio, idioma, centro) se declaran por
NOMBRE DE TABLA. Asi este archivo no importa catalogos/modelos.py y la regla
"nadie importa modelos.py de otro modulo" se cumple de verdad.
"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import EstadoFicha, Formato, LugarClase, Modalidad


class PerfilEstudiante(Base, Marcas):
    """Lo especifico del alumno. Lo comun (correo, clave, nombre) esta en usuario."""

    __tablename__ = "perfil_estudiante"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Datos educativos: son los que muestra la cabecera de 1a y los que usa
    # "Reserva Ya" para prellenar los filtros de 1c.
    etapa_id: Mapped[int | None] = mapped_column(ForeignKey("etapa_educativa.id"))
    nivel: Mapped[str | None] = mapped_column(Text)  # "5.o de bachillerato"
    centro_id: Mapped[int | None] = mapped_column(ForeignKey("centro_educativo.id"))

    # El alumno vive en UN barrio. El plural es del profesor, que son las zonas
    # a las que se traslada (tabla profesor_zona).
    barrio_id: Mapped[int | None] = mapped_column(ForeignKey("barrio.id"))
    direccion: Mapped[str | None] = mapped_column(Text)
    # Sin lat/lon no se lo puede ubicar en el mapa de Leaflet.
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    # Obligatorio si es menor de edad (se sabe por usuario.fecha_nacimiento).
    adulto_nombre: Mapped[str | None] = mapped_column(Text)
    adulto_telefono: Mapped[str | None] = mapped_column(Text)

    # DESNORMALIZADO: lo escribe SOLO el modulo resenas. Es lo que ve el
    # profesor cuando le llega una solicitud en 1i. Calcularlo al vuelo
    # obligaria a recorrer la tabla de resenas en cada consulta de busqueda.
    puntaje_promedio: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    cantidad_resenas: Mapped[int] = mapped_column(nullable=False, default=0)


class PerfilProfesor(Base, Marcas):
    """Lo especifico del profesor: su ficha publica y las reglas de su agenda."""

    __tablename__ = "perfil_profesor"
    __table_args__ = (
        CheckConstraint("duracion_max >= duracion_min", name="duracion_coherente"),
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # --- Presentacion: se ve en 1f, se edita en 1j ---
    titular: Mapped[str | None] = mapped_column(Text)
    biografia: Mapped[str | None] = mapped_column(String(600))
    titulo_habilitante: Mapped[str | None] = mapped_column(Text)
    anios_experiencia: Mapped[int | None] = mapped_column()

    # --- Donde da clase ---
    barrio_id: Mapped[int | None] = mapped_column(ForeignKey("barrio.id"))
    direccion_espacio: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    modalidad: Mapped[Modalidad] = mapped_column(
        Enum(Modalidad, name="modalidad_enum"), nullable=False, default=Modalidad.presencial
    )
    lugar_clase: Mapped[LugarClase] = mapped_column(
        Enum(LugarClase, name="lugar_enum"), nullable=False, default=LugarClase.espacio_propio
    )
    costo_traslado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # --- Precios. NO afectan clases ya creadas: la clase los congela al crearse.
    precio_hora_presencial: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    precio_hora_online: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # --- Reglas que usa agenda para calcular los huecos libres ---
    duracion_min: Mapped[int] = mapped_column(nullable=False, default=60)
    duracion_max: Mapped[int] = mapped_column(nullable=False, default=120)
    descanso_min: Mapped[int] = mapped_column(nullable=False, default=0)
    max_clases_dia: Mapped[int | None] = mapped_column()
    aviso_minimo_horas: Mapped[int] = mapped_column(nullable=False, default=12)

    # --- Grupal: fuera de v1. El formulario de 1j lo guarda y nadie lo lee. ---
    formato: Mapped[Formato] = mapped_column(
        Enum(Formato, name="formato_enum"), nullable=False, default=Formato.individual
    )
    cupo_min: Mapped[int | None] = mapped_column()
    cupo_max: Mapped[int | None] = mapped_column()

    # Solo las publicadas aparecen en la busqueda.
    estado_ficha: Mapped[EstadoFicha] = mapped_column(
        Enum(EstadoFicha, name="ficha_enum"), nullable=False, default=EstadoFicha.borrador
    )

    # DESNORMALIZADO igual que en el perfil del alumno: lo escribe solo resenas.
    puntaje_promedio: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0)
    cantidad_resenas: Mapped[int] = mapped_column(nullable=False, default=0)
    # Lo incrementa clases al marcar una clase como dictada.
    clases_dictadas: Mapped[int] = mapped_column(nullable=False, default=0)


# ---------------------------------------------------------------------------
# La oferta del profesor: cinco tablas de relacion y dos de contenido.
# Son tablas y no columnas porque el filtro de 1c cruza por ellas.
# ---------------------------------------------------------------------------

class ProfesorMateria(Base, Marcas):
    """Que materias dicta. El filtro mas usado de 1c pasa por aca."""

    __tablename__ = "profesor_materia"
    __table_args__ = (UniqueConstraint("perfil_profesor_id", "materia_id"),)

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    materia_id: Mapped[int] = mapped_column(ForeignKey("materia.id"), nullable=False)


class ProfesorEtapa(Base, Marcas):
    """A que etapas le da clase, con el programa que sigue en cada una."""

    __tablename__ = "profesor_etapa"
    __table_args__ = (UniqueConstraint("perfil_profesor_id", "etapa_id"),)

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    etapa_id: Mapped[int] = mapped_column(ForeignKey("etapa_educativa.id"), nullable=False)
    programa: Mapped[str | None] = mapped_column(Text)  # "Plan 2006"


class ProfesorIdioma(Base, Marcas):
    """En que idiomas puede dictar. Uno de los nueve filtros de 1c."""

    __tablename__ = "profesor_idioma"
    __table_args__ = (UniqueConstraint("perfil_profesor_id", "idioma_id"),)

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    idioma_id: Mapped[int] = mapped_column(ForeignKey("idioma.id"), nullable=False)


class ProfesorZona(Base, Marcas):
    """Barrios a los que el profesor se traslada."""

    __tablename__ = "profesor_zona"
    __table_args__ = (UniqueConstraint("perfil_profesor_id", "barrio_id"),)

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    barrio_id: Mapped[int] = mapped_column(ForeignKey("barrio.id"), nullable=False)


class ProfesorDuracion(Base, Marcas):
    """Las duraciones que se le ofrecen al alumno: 60, 90, 120.

    Tabla aparte de duracion_min y duracion_max porque son tres cosas distintas:
    el minimo, el maximo, y la lista concreta de opciones que ve el alumno.
    """

    __tablename__ = "profesor_duracion"
    __table_args__ = (UniqueConstraint("perfil_profesor_id", "minutos"),)

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    minutos: Mapped[int] = mapped_column(nullable=False)


class PuntoMetodo(Base, Marcas):
    """Los puntos de como es una clase conmigo que muestra 1f. Lista ordenada."""

    __tablename__ = "punto_metodo"

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    orden: Mapped[int] = mapped_column(nullable=False, default=0)


class FotoLugar(Base, Marcas):
    """Fotos del espacio donde da clase. Base64, igual que la foto de perfil."""

    __tablename__ = "foto_lugar"

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    imagen_base64: Mapped[str] = mapped_column(Text, nullable=False)
    epigrafe: Mapped[str | None] = mapped_column(Text)
    orden: Mapped[int] = mapped_column(nullable=False, default=0)
    es_portada: Mapped[bool] = mapped_column(nullable=False, default=False)
