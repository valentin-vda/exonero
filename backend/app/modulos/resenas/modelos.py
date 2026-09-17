"""Tablas del modulo resenas - dueno P3.

Una tabla. Las resenas son ANONIMAS y van EN LOS DOS SENTIDOS: el alumno
resena al profesor y el profesor al alumno. Son sobre la persona, no sobre una
clase: una por par y por sentido.

El autor SE GUARDA aunque sean anonimas. Hace falta para dos cosas: impedir
que alguien deje dos resenas a la misma persona, y permitirle editar la suya.
El anonimato se resuelve en la respuesta de la API, no borrando el dato.

Que quede escrito aca, porque si no alguien lo va a exponer sin querer en un GET.
"""

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas
from app.enums import SentidoResena


class Resena(Base, Marcas):
    """Una resena de una persona sobre otra."""

    __tablename__ = "resena"
    __table_args__ = (
        CheckConstraint("puntaje BETWEEN 1 AND 5", name="puntaje_valido"),
        CheckConstraint("autor_id <> destinatario_id", name="no_autorresena"),
        # Lo que hace cumplir la regla de una resena por persona y por sentido.
        # Ademas es lo que permite que GET /clases/mis-profesores y /mis-alumnos
        # devuelvan mi_resena con un LEFT JOIN, en una sola consulta.
        UniqueConstraint("autor_id", "destinatario_id"),
        Index("ix_resena_destinatario", "destinatario_id"),
    )

    # NUNCA SALE EN LA API. Ver el docstring del modulo.
    autor_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    # Las dos apuntan a usuario, porque la resena es sobre la persona y no
    # sobre un rol.
    destinatario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    sentido: Mapped[SentidoResena] = mapped_column(
        Enum(SentidoResena, name="sentido_enum"), nullable=False
    )
    puntaje: Mapped[int] = mapped_column(nullable=False)
    texto: Mapped[str | None] = mapped_column(Text)
