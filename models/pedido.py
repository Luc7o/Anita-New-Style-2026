from datetime import datetime
import uuid
from app_extensions import db

class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id              = db.Column(db.Integer, primary_key=True)
    numero_pedido   = db.Column(db.String(30), unique=True, nullable=False)
    usuario_id      = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Estado del pedido
    ESTADOS = {
        'pendiente':    'Pendiente',
        'confirmado':   'Confirmado',
        'preparando':   'Preparando',
        'enviado':      'Enviado',
        'entregado':    'Entregado',
        'cancelado':    'Cancelado',
    }
    estado = db.Column(db.String(20), default='pendiente')

    # Pago
    METODOS_PAGO = {
        'yape':       'Yape',
        'tarjeta':    'Tarjeta de crédito/débito',
        'efectivo':   'Pago en efectivo',
        'recojo':     'Recojo en tienda',
    }
    ESTADOS_PAGO = {
        'pendiente':  'Pendiente',
        'pagado':     'Pagado',
        'fallido':    'Fallido',
        'reembolsado':'Reembolsado',
    }
    metodo_pago    = db.Column(db.String(20), nullable=False)
    estado_pago    = db.Column(db.String(20), default='pendiente')
    stripe_id      = db.Column(db.String(200))
    comprobante_yape = db.Column(db.String(300))  # imagen del voucher

    # Importes
    subtotal       = db.Column(db.Numeric(10,2), nullable=False)
    costo_envio    = db.Column(db.Numeric(10,2), default=0)
    descuento      = db.Column(db.Numeric(10,2), default=0)
    total          = db.Column(db.Numeric(10,2), nullable=False)

    # Entrega
    TIPOS_ENTREGA = {
        'delivery': 'Delivery a domicilio',
        'recojo':   'Recojo en tienda',
    }
    tipo_entrega   = db.Column(db.String(20), default='delivery')

    # Dirección de envío (copia al momento del pedido)
    envio_nombre   = db.Column(db.String(160))
    envio_telefono = db.Column(db.String(20))
    envio_direccion= db.Column(db.String(200))
    envio_distrito = db.Column(db.String(100))
    envio_provincia= db.Column(db.String(100))
    envio_dpto     = db.Column(db.String(100))
    envio_referencia = db.Column(db.String(200))

    nota           = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualiz = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    detalles = db.relationship('DetallePedido', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def generar_numero():
        return f"ANS-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    @property
    def estado_label(self):
        return self.ESTADOS.get(self.estado, self.estado)

    @property
    def metodo_pago_label(self):
        return self.METODOS_PAGO.get(self.metodo_pago, self.metodo_pago)

    @property
    def estado_pago_label(self):
        return self.ESTADOS_PAGO.get(self.estado_pago, self.estado_pago)

    def __repr__(self):
        return f'<Pedido {self.numero_pedido}>'


class DetallePedido(db.Model):
    __tablename__ = 'detalles_pedido'

    id          = db.Column(db.Integer, primary_key=True)
    pedido_id   = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad    = db.Column(db.Integer, nullable=False, default=1)
    precio_unit = db.Column(db.Numeric(10,2), nullable=False)
    talla       = db.Column(db.String(20))
    color       = db.Column(db.String(50))
    subtotal    = db.Column(db.Numeric(10,2), nullable=False)

    def __repr__(self):
        return f'<DetallePedido pedido={self.pedido_id} prod={self.producto_id}>'
