"""Agrega columnas 2FA al modelo Usuario

Revision ID: 002_2fa
Revises: 001_almacen
Create Date: 2026-01-01 00:00:01.000000
"""
from alembic import op
import sqlalchemy as sa

revision      = '002_2fa'
down_revision = '001_almacen'
branch_labels = None
depends_on    = None


def upgrade():
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.add_column(sa.Column('codigo_2fa',        sa.String(6)))
        batch_op.add_column(sa.Column('codigo_2fa_expira', sa.DateTime()))


def downgrade():
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.drop_column('codigo_2fa_expira')
        batch_op.drop_column('codigo_2fa')
