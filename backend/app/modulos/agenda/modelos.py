"""Tablas del modulo agenda - dueno P3.

Dos tablas, y son las dos caras de la misma pregunta: cuando puede el profesor.

  franja_disponibilidad  cuando SI puede, repetido todas las semanas
                         ("martes de 14 a 18")
  bloqueo                la excepcion puntual, con fecha
                         ("el 12 de mayo no puedo")

La disponibilidad se guarda EN POSITIVO. El esquema viejo del equipo tenia
"horarios no disponibles" y con eso no se puede dibujar el calendario de 1f:
no hay forma de saber si un hueco vacio es que puede o que nunca dijo nada.
"""

from datetime import datetime, time

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import Modalidad


class FranjaDisponibilidad(Base, Marcas):
    """Una franja semanal recurrente. Se edita desde 1i y tambien desde 1j."""

    __tablename__ = "franja_disponibilidad"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="dia_valido"),
        CheckConstraint("hora_fin > hora_inicio", name="franja_valida"),
        # El calculo de huecos libres pide las franjas de un profesor por dia.
        Index("ix_franja_profesor_dia", "perfil_profesor_id", "dia_semana"),
    )

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    # 0 = domingo ... 6 = sabado. Mismo criterio que JavaScript Date.getDay(),
    # asi el frontend no tiene que convertir nada.
    dia_semana: Mapped[int] = mapped_column(nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    # Un profesor puede ofrecer online de noche y presencial solo de tarde.
    modalidad: Mapped[Modalidad] = mapped_column(
        Enum(Modalidad, name="modalidad_enum"), nullable=False, default=Modalidad.ambas
    )
    # Apagar una franja sin borrarla, para las vacaciones.
    activa: Mapped[bool] = mapped_column(nullable=False, default=True)


class Bloqueo(Base, Marcas):
    """Una excepcion puntual con fecha: tapa lo que diga la franja semanal."""

    __tablename__ = "bloqueo"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="bloqueo_valido"),
        Index("ix_bloqueo_profesor_inicio", "perfil_profesor_id", "inicio"),
    )

    perfil_profesor_id: Mapped[int] = mapped_column(
        ForeignKey("perfil_profesor.id", ondelete="CASCADE"), nullable=False
    )
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    motivo: Mapped[str | None] = mapped_column(Text)
