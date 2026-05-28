"""Integración módulo almacén: proveedores, movimientos_stock, ventas_fisicas

Revision ID: 001_almacen
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '001_almacen'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── Tabla proveedores ────────────────────────────────────────────────────
    op.create_table(
        'proveedores',
        sa.Column('id',             sa.Integer(),     primary_key=True),
        sa.Column('nombre',         sa.String(150),   nullable=False),
        sa.Column('ruc',            sa.String(11),    unique=True),
        sa.Column('contacto',       sa.String(100)),
        sa.Column('telefono',       sa.String(20)),
        sa.Column('email',          sa.String(150)),
        sa.Column('direccion',      sa.String(250)),
        sa.Column('activo',         sa.Boolean(),     default=True),
        sa.Column('notas',          sa.Text()),
        sa.Column('fecha_registro', sa.DateTime()),
    )

    # ── Columnas nuevas en productos ─────────────────────────────────────────
    with op.batch_alter_table('productos') as batch_op:
        batch_op.add_column(sa.Column('precio_compra', sa.Numeric(10, 2), server_default='0'))
        batch_op.add_column(sa.Column('stock_minimo',  sa.Integer(),       server_default='5'))
        batch_op.add_column(sa.Column('codigo_barras', sa.String(100)))
        batch_op.add_column(sa.Column('unidad',        sa.String(30),      server_default='unidad'))
        batch_op.add_column(sa.Column('proveedor_id',  sa.Integer(),       sa.ForeignKey('proveedores.id'), nullable=True))

    # ── Tabla movimientos_stock ──────────────────────────────────────────────
    op.create_table(
        'movimientos_stock',
        sa.Column('id',           sa.Integer(),    primary_key=True),
        sa.Column('producto_id',  sa.Integer(),    sa.ForeignKey('productos.id'), nullable=False),
        sa.Column('tipo',         sa.String(20),   nullable=False),
        sa.Column('cantidad',     sa.Integer(),    nullable=False),
        sa.Column('stock_antes',  sa.Integer(),    nullable=False),
        sa.Column('stock_despues',sa.Integer(),    nullable=False),
        sa.Column('motivo',       sa.String(250)),
        sa.Column('referencia',   sa.String(100)),
        sa.Column('proveedor_id', sa.Integer(),    sa.ForeignKey('proveedores.id'), nullable=True),
        sa.Column('usuario_id',   sa.Integer(),    sa.ForeignKey('usuarios.id'),   nullable=True),
        sa.Column('fecha',        sa.DateTime()),
    )

    # ── Tabla ventas_fisicas ─────────────────────────────────────────────────
    op.create_table(
        'ventas_fisicas',
        sa.Column('id',             sa.Integer(),        primary_key=True),
        sa.Column('numero_venta',   sa.String(30),       unique=True, nullable=False),
        sa.Column('cliente_nombre', sa.String(150)),
        sa.Column('cliente_doc',    sa.String(15)),
        sa.Column('metodo_pago',    sa.String(20),       nullable=False, server_default='efectivo'),
        sa.Column('subtotal',       sa.Numeric(10, 2),   nullable=False),
        sa.Column('descuento',      sa.Numeric(10, 2),   server_default='0'),
        sa.Column('total',          sa.Numeric(10, 2),   nullable=False),
        sa.Column('notas',          sa.Text()),
        sa.Column('usuario_id',     sa.Integer(),        sa.ForeignKey('usuarios.id'), nullable=True),
        sa.Column('fecha',          sa.DateTime()),
        sa.Column('anulada',        sa.Boolean(),        server_default='0'),
    )

    # ── Tabla detalles_venta ─────────────────────────────────────────────────
    op.create_table(
        'detalles_venta',
        sa.Column('id',          sa.Integer(),      primary_key=True),
        sa.Column('venta_id',    sa.Integer(),      sa.ForeignKey('ventas_fisicas.id'), nullable=False),
        sa.Column('producto_id', sa.Integer(),      sa.ForeignKey('productos.id'),      nullable=False),
        sa.Column('cantidad',    sa.Integer(),      nullable=False, server_default='1'),
        sa.Column('precio_unit', sa.Numeric(10, 2), nullable=False),
        sa.Column('talla',       sa.String(20)),
        sa.Column('color',       sa.String(50)),
        sa.Column('subtotal',    sa.Numeric(10, 2), nullable=False),
    )


def downgrade():
    op.drop_table('detalles_venta')
    op.drop_table('ventas_fisicas')
    op.drop_table('movimientos_stock')
    with op.batch_alter_table('productos') as batch_op:
        batch_op.drop_column('proveedor_id')
        batch_op.drop_column('unidad')
        batch_op.drop_column('codigo_barras')
        batch_op.drop_column('stock_minimo')
        batch_op.drop_column('precio_compra')
    op.drop_table('proveedores')
