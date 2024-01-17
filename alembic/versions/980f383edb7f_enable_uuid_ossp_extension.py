"""enable uuid ossp extension

Revision ID: 980f383edb7f
Revises: 
Create Date: 2024-01-18 01:26:40.594876

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '980f383edb7f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")


def downgrade() -> None:
    pass
