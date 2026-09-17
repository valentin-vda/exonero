"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Fecha: ${create_date}

RECORDATORIO: leer lo que genero el autogenerador antes de subir esto.
Alembic interpreta un renombre de columna como un DROP + ADD, y con eso se
pierden los datos. Si ves un drop_column que no pediste, corregilo a mano.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
