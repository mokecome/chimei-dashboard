"""Update file status enum from PROCESSING to ANALYZING

Revision ID: 128711c8492e
Revises: 940f422d0a05
Create Date: 2025-07-28 18:17:32.191157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '128711c8492e'
down_revision: Union[str, None] = '940f422d0a05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # First, update any existing PROCESSING records to ANALYZING
    op.execute("UPDATE voice_files SET status = 'analyzing' WHERE status = 'processing'")
    
    # Recreate the enum with new value
    op.execute("ALTER TABLE voice_files MODIFY COLUMN status ENUM('pending', 'analyzing', 'completed', 'failed') NOT NULL")


def downgrade() -> None:
    """Downgrade database schema."""
    # Update ANALYZING back to PROCESSING for downgrade
    op.execute("UPDATE voice_files SET status = 'processing' WHERE status = 'analyzing'")
    
    # Recreate the enum with old value
    op.execute("ALTER TABLE voice_files MODIFY COLUMN status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL")