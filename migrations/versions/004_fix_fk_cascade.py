"""Arreglar FKs para agregar ON DELETE CASCADE en MySQL

Revision ID: 004_fix_fk_cascade
Revises: 003_reset_password
Create Date: 2026-05-28 00:00:00.000000

IMPORTANTE: Esta migración recrea las foreign keys con ON DELETE CASCADE.
Esto permite borrar usuarios y pedidos sin errores de constraint en MySQL.
"""
from alembic import op
import sqlalchemy as sa

revision = '004_fix_fk_cascade'
down_revision = '003_reset_password'
branch_labels = None
depends_on = None


def upgrade():
    # ── pedidos.usuario_id → usuarios.id ─────────────────────────────────────
    # 1. Eliminar FK antigua
    op.drop_constraint('pedidos_ibfk_1', 'pedidos', type_='foreignkey')
    # 2. Recrear con ON DELETE CASCADE
    op.create_foreign_key(
        'pedidos_ibfk_1',
        'pedidos', 'usuarios',
        ['usuario_id'], ['id'],
        ondelete='CASCADE'
    )

    # ── detalles_pedido.pedido_id → pedidos.id ────────────────────────────────
    op.drop_constraint('detalles_pedido_ibfk_1', 'detalles_pedido', type_='foreignkey')
    op.create_foreign_key(
        'detalles_pedido_ibfk_1',
        'detalles_pedido', 'pedidos',
        ['pedido_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Revertir a FKs sin CASCADE
    op.drop_constraint('detalles_pedido_ibfk_1', 'detalles_pedido', type_='foreignkey')
    op.create_foreign_key(
        'detalles_pedido_ibfk_1',
        'detalles_pedido', 'pedidos',
        ['pedido_id'], ['id']
    )

    op.drop_constraint('pedidos_ibfk_1', 'pedidos', type_='foreignkey')
    op.create_foreign_key(
        'pedidos_ibfk_1',
        'pedidos', 'usuarios',
        ['usuario_id'], ['id']
    )
