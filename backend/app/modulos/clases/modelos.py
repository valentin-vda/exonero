"""Tablas del modulo clases - dueno P4.

Una sola tabla, pero es la mas importante del sistema: LA CLASE ES LA RESERVA.

No hay tabla de reservas. Se crea directamente una clase en estado pendiente;
el profesor la aprueba y pasa a aprobada, o la rechaza y la fila SE BORRA.
Cancelar no borra: cambia el estado, porque el historial de 1b, la tasa de
cancelacion de 1d y el reembolso lo necesitan.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import Actor, EstadoClase, Modalidad


class Clase(Base, Marcas):
    """Una clase entre un alumno y un profesor."""

    __tablename__ = "clase"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="clase_valida"),
        CheckConstraint("estudiante_id <> profesor_id", name="partes_distintas"),
        # Una clase concreta es presencial u online. 'ambas' es una preferencia
        # del perfil, no algo que pueda pasarle a una clase real.
        CheckConstraint("modalidad IN ('presencial','online')", name="modalidad_concreta"),
        # El indice mas usado del sistema: calendario del profesor, calculo de
        # huecos libres y deteccion de superposicion.
        Index("ix_clase_profesor_inicio", "profesor_id", "inicio"),
        Index("ix_clase_estudiante_inicio", "estudiante_id", "inicio"),
        Index("ix_clase_estado", "estado"),
    )

    # Las dos partes apuntan a usuario, no a los perfiles: una clase es entre
    # dos personas.
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    profesor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)

    # El mockup los muestra en cada tarjeta de clase.
    materia_id: Mapped[int | None] = mapped_column(ForeignKey("materia.id"))
    etapa_id: Mapped[int | None] = mapped_column(ForeignKey("etapa_educativa.id"))
    tema: Mapped[str | None] = mapped_column(Text)  # que quiere trabajar el alumno

    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duracion_min: Mapped[int] = mapped_column(nullable=False)
    # Se calcula al insertar (inicio + duracion). Existe como columna y no se
    # deduce al vuelo porque es lo que se cruza para detectar superposiciones.
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    modalidad: Mapped[Modalidad] = mapped_column(
        Enum(Modalidad, name="modalidad_enum"), nullable=False
    )
    ubicacion: Mapped[str | None] = mapped_column(Text)  # direccion o enlace

    estado: Mapped[EstadoClase] = mapped_column(
        Enum(EstadoClase, name="clase_enum"), nullable=False, default=EstadoClase.pendiente
    )
    motivo: Mapped[str | None] = mapped_column(Text)  # de la cancelacion
    cancelada_por: Mapped[Actor | None] = mapped_column(Enum(Actor, name="actor_enum"))

    # ---------------------------------------------------------------------
    # DESGLOSE CONGELADO AL CREAR.
    # Si manana el profesor sube su precio o cambia la comision, esta clase
    # sigue valiendo lo mismo y el comprobante sigue cuadrando. Por eso son
    # columnas de la clase y no se leen del perfil cada vez.
    # ---------------------------------------------------------------------
    precio_hora: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    costo_traslado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    pct_comision: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    pct_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    impuesto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


# ---------------------------------------------------------------------------
# La restriccion EXCLUDE va en la migracion de Alembic, escrita a mano:
#
#   ALTER TABLE clase ADD CONSTRAINT clase_sin_superposicion
#   EXCLUDE USING gist (profesor_id WITH =, tstzrange(inicio, fin) WITH &&)
#   WHERE (estado = 'aprobada');
#
# Es lo UNICO que impide de verdad que dos alumnos confirmen el mismo horario
# en el mismo instante. Validarlo solo en Python deja una ventana de carrera
# que en la demostracion se puede notar. Solo aplica a las aprobadas: varias
# solicitudes pendientes sobre el mismo hueco son legitimas.
#
# Necesita la extension btree_gist, que crea backend/docker/init.sql.
# ---------------------------------------------------------------------------
