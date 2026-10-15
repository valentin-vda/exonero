"""Tablas del modulo mensajeria - dueno P3.

Dos tablas: hilo y mensaje. Chat directo entre un alumno y un profesor, sin
contexto de clase y sin reservar desde ahi (las dos cosas quedaron fuera de
alcance).

El chat es la razon por la que existe una sola tabla usuario: si estudiante y
profesor fueran dos tablas paralelas, no habria de donde colgar el hilo, que
une a los dos.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas


class Hilo(Base, Marcas):
    """Una conversacion entre un alumno y un profesor. Hay una sola por par."""

    __tablename__ = "hilo"
    __table_args__ = (
        # Por esto POST /mensajes/hilos devuelve siempre el mismo hilo en vez
        # de crear uno nuevo cada vez que entran desde 1f.
        UniqueConstraint("estudiante_id", "profesor_id"),
    )

    estudiante_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    profesor_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )

    # DESNORMALIZADO: es por lo que se ordena la bandeja de 1h. Calcularlo con
    # un MAX(enviado_el) por cada hilo en cada carga seria caro. Lo escribe el
    # propio modulo al enviar un mensaje.
    ultimo_mensaje_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Mensaje(Base, Marcas):
    """Un mensaje dentro de un hilo."""

    __tablename__ = "mensaje"
    __table_args__ = (
        Index("ix_mensaje_hilo_enviado", "hilo_id", "enviado_el"),
        # Indice parcial: solo indexa los sin leer, que son pocos. Es lo que
        # hace barato el contador de la cabecera, que se consulta cada diez
        # segundos desde las diez pantallas.
        # OJO: text() en minuscula (una expresion SQL), no Text (el tipo de
        # columna). Con Text la migracion generada no corre.
        Index("ix_mensaje_sin_leer", "hilo_id", postgresql_where=text("leido_el IS NULL")),
    )

    hilo_id: Mapped[int] = mapped_column(ForeignKey("hilo.id", ondelete="CASCADE"), nullable=False)
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    enviado_el: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # NULL = sin leer. Se completa al abrir el hilo, en el mismo GET que trae
    # los mensajes: no hay una accion aparte de "marcar como leido".
    leido_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
