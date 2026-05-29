"""Crea tabla codigo_2fa y elimina columnas 2FA de usuarios

Revision ID: 005_codigo_2fa
Revises: 004_fix_fk_cascade
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa

revision      = '005_codigo_2fa'
down_revision = '004_fix_fk_cascade'
branch_labels = None
depends_on    = None


def upgrade():
    # 1. Crear la nueva tabla
    op.create_table(
        'codigos_2fa',
        sa.Column('id',         sa.Integer(),  primary_key=True),
        sa.Column('usuario_id', sa.Integer(),  sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('codigo',     sa.String(6),  nullable=False),
        sa.Column('expira_en',  sa.DateTime(), nullable=False),
        sa.Column('usado',      sa.Boolean(),  nullable=False, server_default=sa.false()),
        sa.Column('creado_en',  sa.DateTime(), server_default=sa.func.now()),
    )

    # 2. Eliminar las columnas 2FA que estaban en usuarios
    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.drop_column('codigos_2fa')
        batch_op.drop_column('codigos_2fa_expira')


def downgrade():
    # Invertir: eliminar tabla y restaurar columnas
    op.drop_table('codigos_2fa')

    with op.batch_alter_table('usuarios') as batch_op:
        batch_op.add_column(sa.Column('codigos_2fa',        sa.String(6)))
        batch_op.add_column(sa.Column('codigos_2fa_expira', sa.DateTime()))
