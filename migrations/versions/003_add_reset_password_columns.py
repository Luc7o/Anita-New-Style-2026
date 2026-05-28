"""Agregar columnas de recuperación de contraseña al modelo Usuario

Revision ID: 003_reset_password
Revises: 002_add_2fa_columns
Create Date: 2026-05-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003_reset_password'
down_revision = '002_2fa'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.add_column(sa.Column('reset_token',        sa.String(100), unique=True, nullable=True))
        batch_op.add_column(sa.Column('reset_token_expira', sa.DateTime(),  nullable=True))
    # Índice para búsquedas rápidas por token
    op.create_index('ix_usuarios_reset_token', 'usuarios', ['reset_token'], unique=True)


def downgrade():
    op.drop_index('ix_usuarios_reset_token', table_name='usuarios')
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.drop_column('reset_token')
        batch_op.drop_column('reset_token_expira')
