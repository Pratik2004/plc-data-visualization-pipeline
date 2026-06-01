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
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
    
    # Drop the serial ID primary key to allow time-based partitioning
    op.execute("ALTER TABLE readings DROP CONSTRAINT readings_pkey CASCADE")
    
    # Add a composite primary key that includes the time column (required for hypertable)
    op.execute("ALTER TABLE readings ADD PRIMARY KEY (time, tagid)")
    
    # Create the hypertable
    op.execute("SELECT create_hypertable('readings', 'time', if_not_exists => TRUE)")
    
    # Enable compression
    op.execute("ALTER TABLE readings SET (timescaledb.compress, timescaledb.compress_segmentby = 'tagid')")
    
    # Add compression policy
    op.execute("SELECT add_compression_policy('readings', INTERVAL '30 days', if_not_exists => true)")


def downgrade() -> None:
    """Downgrade schema."""
    # Safe downgrade that checks if operations exist
    op.execute("""
        DO $$
        BEGIN
            PERFORM remove_compression_policy('readings', if_not_exists => true);
        EXCEPTION WHEN undefined_function THEN
            NULL;
        END
        $$;
    """)
