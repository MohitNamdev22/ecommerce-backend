"""Product Model Updated

Revision ID: 8f232d46e48a
Revises: e4b6f2346fe5
Create Date: 2025-06-09 22:23:20.762716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f232d46e48a'
down_revision: Union[str, None] = 'e4b6f2346fe5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('products', 'image_url')
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('products', sa.Column('image_url', sa.String(length=255), nullable=True))

    pass
