"""Add archived to Item

Revision ID: b7c3a9d4e1f2
Revises: fe56fa70289e
Create Date: 2026-10-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c3a9d4e1f2'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'item',
        sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('item', 'archived')
