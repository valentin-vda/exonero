"""privacidad y consentimiento parental

Revision ID: b18c331
Revises: 5a01195bec7c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b18c331"
down_revision: Union[str, None] = "5a01195bec7c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE estado_cuenta_enum ADD VALUE IF NOT EXISTS 'pendiente_consentimiento_parental'")
    op.execute("ALTER TYPE estado_cuenta_enum ADD VALUE IF NOT EXISTS 'anonimizada'")
    op.add_column("usuario", sa.Column("version_sesion", sa.Integer(), server_default="0", nullable=False))
    op.add_column("usuario", sa.Column("anonimizado_el", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "consentimiento",
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("version_documento", sa.Text(), nullable=False),
        sa.Column("hash_documento", sa.Text(), nullable=False),
        sa.Column("aceptado_el", sa.DateTime(timezone=True), nullable=False),
        sa.Column("aceptado_por", sa.Text(), nullable=False),
        sa.Column("adulto_nombre", sa.Text()),
        sa.Column("adulto_correo", sa.Text()),
        sa.Column("adulto_vinculo", sa.Text()),
        sa.Column("ip", sa.Text()),
        sa.Column("agente_usuario", sa.Text()),
        sa.Column("revocado_el", sa.DateTime(timezone=True)),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creado_el", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_el", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_consentimiento_usuario_id", "consentimiento", ["usuario_id"])

    op.create_table(
        "invitacion_parental",
        sa.Column("usuario_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("correo_adulto", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expira_el", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usada_el", sa.DateTime(timezone=True)),
        sa.Column("enviado_el", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creado_el", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_el", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "auditoria_privacidad",
        sa.Column("usuario_id", sa.Integer()),
        sa.Column("evento", sa.Text(), nullable=False),
        sa.Column("detalle", sa.Text()),
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creado_el", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("actualizado_el", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_auditoria_privacidad_usuario_id", "auditoria_privacidad", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_auditoria_privacidad_usuario_id", table_name="auditoria_privacidad")
    op.drop_table("auditoria_privacidad")
    op.drop_table("invitacion_parental")
    op.drop_index("ix_consentimiento_usuario_id", table_name="consentimiento")
    op.drop_table("consentimiento")
    op.drop_column("usuario", "anonimizado_el")
    op.drop_column("usuario", "version_sesion")
    op.execute("UPDATE usuario SET estado='dada_de_baja' WHERE estado::text IN ('pendiente_consentimiento_parental','anonimizada')")
    op.execute("ALTER TYPE estado_cuenta_enum RENAME TO estado_cuenta_enum_old")
    op.execute("CREATE TYPE estado_cuenta_enum AS ENUM ('activa','dada_de_baja')")
    op.execute("ALTER TABLE usuario ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE usuario ALTER COLUMN estado TYPE estado_cuenta_enum USING estado::text::estado_cuenta_enum")
    op.execute("ALTER TABLE usuario ALTER COLUMN estado SET DEFAULT 'activa'::estado_cuenta_enum")
    op.execute("DROP TYPE estado_cuenta_enum_old")
