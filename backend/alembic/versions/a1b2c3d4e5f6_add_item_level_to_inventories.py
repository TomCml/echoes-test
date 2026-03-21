"""Add item_level and item_xp to inventories

Revision ID: a1b2c3d4e5f6
Revises: c994f132fa10
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c994f132fa10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inventories', sa.Column('item_level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('inventories', sa.Column('item_xp', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('inventories', 'item_xp')
    op.drop_column('inventories', 'item_level')
