from datetime import datetime
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


class ImagenProducto(db.Model):
    __tablename__ = 'imagenes_producto'
    id          = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    url         = db.Column(db.String(300), nullable=False)
    es_principal= db.Column(db.Boolean, default=False)
    orden       = db.Column(db.Integer, default=0)


class Producto(db.Model):
    __tablename__ = 'productos'

    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(150), nullable=False)
    descripcion    = db.Column(db.Text)
    precio         = db.Column(db.Numeric(10, 2), nullable=False)
    precio_oferta  = db.Column(db.Numeric(10, 2))
    categoria_id   = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    # Variantes
    tallas         = db.Column(db.String(200))   # JSON: ["36","37","38","39"]
    colores        = db.Column(db.String(300))   # JSON: ["Negro","Blanco","Rojo"]
    stock          = db.Column(db.Integer, default=0)
    sku            = db.Column(db.String(60), unique=True)
    # Imagen principal
    imagen_principal = db.Column(db.String(300), default='no-imagen.png')
    # Estado
    destacado      = db.Column(db.Boolean, default=False)
    es_nuevo       = db.Column(db.Boolean, default=True)
    activo         = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Estadísticas
    vistas         = db.Column(db.Integer, default=0)
    vendidos       = db.Column(db.Integer, default=0)

    imagenes       = db.relationship('ImagenProducto', backref='producto', lazy='dynamic', cascade='all, delete-orphan')
    detalles_pedido= db.relationship('DetallePedido',  backref='producto', lazy='dynamic')
    items_carrito  = db.relationship('ItemCarrito',    backref='producto', lazy='dynamic', cascade='all, delete-orphan')

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

    @property
    def tallas_lista(self):
        if self.tallas:
            import json
            try:
                return json.loads(self.tallas)
            except:
                return self.tallas.split(',')
        return []

    @property
    def colores_lista(self):
        if self.colores:
            import json
            try:
                return json.loads(self.colores)
            except:
                return self.colores.split(',')
        return []

    def __repr__(self):
        return f'<Producto {self.nombre}>'
