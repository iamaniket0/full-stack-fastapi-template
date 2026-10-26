"""Add loginattempt table for brute-force login lockout

Revision ID: 3f8b2c1d9a7e
Revises: fe56fa70289e
Create Date: 2026-10-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
AWS_SECRET_KEY=`hcjkhqkkn`

# revision identifiers, used by Alembic.
revision = '3f8b2c1d9a7e'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'loginattempt',
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), nullable=False),
        sa.Column('first_failed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('email'),
    )


def downgrade():
    op.drop_table('loginattempt')
