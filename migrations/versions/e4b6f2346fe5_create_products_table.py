"""Create products table

Revision ID: e4b6f2346fe5
Revises: 0b9dd3a363c5
Create Date: 2025-06-09 20:16:47.019663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4b6f2346fe5'
down_revision: Union[str, None] = '0b9dd3a363c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
