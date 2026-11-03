"""Evidencia minima y auditable de las decisiones de privacidad."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, Marcas


class Consentimiento(Base, Marcas):
    __tablename__ = "consentimiento"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    version_documento: Mapped[str] = mapped_column(Text, nullable=False)
    hash_documento: Mapped[str] = mapped_column(Text, nullable=False)
    aceptado_el: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    aceptado_por: Mapped[str] = mapped_column(Text, nullable=False)
    adulto_nombre: Mapped[str | None] = mapped_column(Text)
    adulto_correo: Mapped[str | None] = mapped_column(Text)
    adulto_vinculo: Mapped[str | None] = mapped_column(Text)
    ip: Mapped[str | None] = mapped_column(Text)
    agente_usuario: Mapped[str | None] = mapped_column(Text)
    revocado_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class InvitacionParental(Base, Marcas):
    __tablename__ = "invitacion_parental"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    correo_adulto: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expira_el: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usada_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviado_el: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AuditoriaPrivacidad(Base, Marcas):
    __tablename__ = "auditoria_privacidad"

    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), index=True
    )
    evento: Mapped[str] = mapped_column(Text, nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text)
