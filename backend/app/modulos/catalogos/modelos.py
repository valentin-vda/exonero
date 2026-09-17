"""Tablas del modulo catalogos · dueno P2.

Seis tablas de listas fijas que referencia medio modelo: materias, etapas,
centros, barrios, idiomas y los parametros de plataforma (comision e IVA).

Las referencia medio sistema, pero ningun otro modulo importa este archivo:
las claves foraneas se declaran por nombre de tabla, ForeignKey("barrio.id").
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import ARRAY, Date, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import TipoCentro


class Barrio(Base, Marcas):
    """Barrios de Montevideo. latitud/longitud son el centroide: con eso
    Leaflet centra la vista inicial del mapa (1a y 1c)."""

    __tablename__ = "barrio"

    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    departamento: Mapped[str] = mapped_column(Text, nullable=False, default="Montevideo")
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))


class EtapaEducativa(Base, Marcas):
    """Ciclo basico, bachillerato, UTU, universidad, examen de ingreso.

    OJO: esta lista es la que manda. El esquema viejo del equipo decia
    escuela/liceo/orientacion/facultad y el mockup filtra por otra cosa; todo
    el filtrado de 1c depende de que sea una sola lista.
    """

    __tablename__ = "etapa_educativa"

    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    orden: Mapped[int] = mapped_column(nullable=False, default=0)
    # {'1.º','2.º','3.º'} — los niveles dentro de la etapa
    niveles: Mapped[list[str] | None] = mapped_column(ARRAY(Text))


class CentroEducativo(Base, Marcas):
    """Liceos, UTUs y facultades. Tiene coordenadas porque el carrusel
    'cerca de mi centro' de 1a las necesita."""

    __tablename__ = "centro_educativo"

    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[TipoCentro] = mapped_column(
        Enum(TipoCentro, name="centro_enum"), nullable=False
    )
    barrio_id: Mapped[int | None] = mapped_column(ForeignKey("barrio.id"))
    direccion: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))


class Materia(Base, Marcas):
    """Matematica, Fisica, Quimica, Idioma Espanol, Ingles, Historia..."""

    __tablename__ = "materia"

    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    nombre_corto: Mapped[str | None] = mapped_column(Text)
    activa: Mapped[bool] = mapped_column(nullable=False, default=True)


class Idioma(Base, Marcas):
    """Idioma en el que el profesor puede dar la clase (uno de los 9 filtros)."""

    __tablename__ = "idioma"

    nombre: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class ParametroPlataforma(Base, Marcas):
    """Comision de servicio y tasa de IVA.

    En tabla y no como constante en el codigo: se cambian sin recompilar y
    quedan versionadas por fecha. De aca salen los porcentajes que congela
    cada clase al crearse.
    """

    __tablename__ = "parametro_plataforma"
    __table_args__ = (UniqueConstraint("clave", "vigente_desde"),)

    clave: Mapped[str] = mapped_column(Text, nullable=False)  # comision_servicio | tasa_iva
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False, server_default="CURRENT_DATE")
