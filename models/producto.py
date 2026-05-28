from datetime import datetime
import json
from app_extensions import db


class Categoria(db.Model):
    __tablename__ = 'categorias'
    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(80), nullable=False, unique=True)
    slug        = db.Column(db.String(80), nullable=False, unique=True)
    descripcion = db.Column(db.String(300))
    icono       = db.Column(db.String(100), default='bag')
    activo      = db.Column(db.Boolean, default=True)
    productos   = db.relationship('Producto', backref='categoria_rel', lazy='dynamic')

    CATEGORIAS_DEFAULT = [
        ('Calzados',    'calzados',   'boot'),
        ('Vestidos',    'vestidos',   'dress'),
        ('Carteras',    'carteras',   'handbag'),
        ('Mochilas',    'mochilas',   'backpack'),
        ('Accesorios',  'accesorios', 'gem'),
    ]

    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(150), nullable=False)
    ruc            = db.Column(db.String(11), unique=True)
    contacto       = db.Column(db.String(100))
    telefono       = db.Column(db.String(20))
    email          = db.Column(db.String(150))
    direccion      = db.Column(db.String(250))
    activo         = db.Column(db.Boolean, default=True)
    notas          = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    productos   = db.relationship('Producto', backref='proveedor', lazy='dynamic')

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'


class ImagenProducto(db.Model):
    __tablename__ = 'imagenes_producto'
    id          = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    url         = db.Column(db.String(300), nullable=False)
    es_principal= db.Column(db.Boolean, default=False)
    orden       = db.Column(db.Integer, default=0)


class Producto(db.Model):
    __tablename__ = 'productos'

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(150), nullable=False)
    descripcion     = db.Column(db.Text)

    # Precios — tienda online
    precio          = db.Column(db.Numeric(10, 2), nullable=False)
    precio_oferta   = db.Column(db.Numeric(10, 2))

    # Precio de compra — almacén
    precio_compra   = db.Column(db.Numeric(10, 2), default=0)

    # Stock
    stock           = db.Column(db.Integer, default=0)
    stock_minimo    = db.Column(db.Integer, default=5)

    # Identificadores
    sku             = db.Column(db.String(60), unique=True)
    codigo_barras   = db.Column(db.String(100))

    # Variantes
    tallas          = db.Column(db.String(200))
    colores         = db.Column(db.String(300))
    unidad          = db.Column(db.String(30), default='unidad')

    # Relaciones
    categoria_id    = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    proveedor_id    = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=True)

    # Imagen
    imagen_principal = db.Column(db.String(300), default='no-imagen.png')

    # Flags tienda online
    destacado       = db.Column(db.Boolean, default=False)
    es_nuevo        = db.Column(db.Boolean, default=True)
    activo          = db.Column(db.Boolean, default=True)

    # Estadísticas
    vistas          = db.Column(db.Integer, default=0)
    vendidos        = db.Column(db.Integer, default=0)

    # Fechas
    fecha_creacion      = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    imagenes        = db.relationship('ImagenProducto', backref='producto', lazy='dynamic',
                                      cascade='all, delete-orphan')
    detalles_pedido = db.relationship('DetallePedido', backref='producto', lazy='dynamic')
    items_carrito   = db.relationship('ItemCarrito',   backref='producto', lazy='dynamic',
                                      cascade='all, delete-orphan')

    # ── Propiedades tienda online ──────────────────────────────────────────────

    @property
    def precio_final(self):
        return float(self.precio_oferta) if self.precio_oferta else float(self.precio)

    @property
    def tiene_oferta(self):
        return self.precio_oferta is not None and float(self.precio_oferta) < float(self.precio)

    @property
    def descuento_porcentaje(self):
        if self.tiene_oferta:
            desc = (float(self.precio) - float(self.precio_oferta)) / float(self.precio) * 100
            return round(desc)
        return 0

    # ── Propiedades almacén ────────────────────────────────────────────────────

    @property
    def precio_venta(self):
        """Alias para compatibilidad con módulo de almacén."""
        return self.precio_final

    @property
    def stock_bajo(self):
        return self.stock > 0 and self.stock <= self.stock_minimo

    @property
    def sin_stock(self):
        return self.stock <= 0

    @property
    def margen(self):
        if self.precio_compra and float(self.precio_compra) > 0:
            return round(
                (float(self.precio) - float(self.precio_compra)) / float(self.precio_compra) * 100, 1
            )
        return None

    @property
    def valor_inventario(self):
        return float(self.precio) * self.stock

    @property
    def categoria(self):
        """Alias corto para templates de almacén."""
        return self.categoria_rel

    # ── Propiedades variantes ──────────────────────────────────────────────────

    @property
    def tallas_lista(self):
        if self.tallas:
            try:
                return json.loads(self.tallas)
            except Exception:
                return self.tallas.split(',')
        return []

    @property
    def colores_lista(self):
        if self.colores:
            try:
                return json.loads(self.colores)
            except Exception:
                return self.colores.split(',')
        return []

    def __repr__(self):
        return f'<Producto {self.nombre}>'
