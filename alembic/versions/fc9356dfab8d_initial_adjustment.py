"""Initial adjustment

Revision ID: fc9356dfab8d
Revises: aa6f34364624
Create Date: 2025-05-21 05:35:45.089236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc9356dfab8d'
down_revision: Union[str, None] = 'aa6f34364624'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
