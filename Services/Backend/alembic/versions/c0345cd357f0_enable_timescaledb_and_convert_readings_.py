"""enable timescaledb and convert readings to hypertable

Revision ID: c0345cd357f0
Revises: 0ef69a51642f
Create Date: 2026-05-16 17:13:06.745139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0345cd357f0'
down_revision: Union[str, Sequence[str], None] = '0ef69a51642f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
