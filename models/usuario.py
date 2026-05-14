from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app_extensions import db

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(80), nullable=False)
    apellido       = db.Column(db.String(80), nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash  = db.Column(db.String(512), nullable=False)
    telefono       = db.Column(db.String(20))
    dni            = db.Column(db.String(15))
    # Dirección
    direccion      = db.Column(db.String(200))
    distrito       = db.Column(db.String(100))
    provincia      = db.Column(db.String(100))
    departamento   = db.Column(db.String(100))
    referencia     = db.Column(db.String(200))
    # Control
    es_admin       = db.Column(db.Boolean, default=False)
    activo         = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso  = db.Column(db.DateTime)
    foto_perfil    = db.Column(db.String(200), default='default_avatar.png')

    pedidos   = db.relationship('Pedido',      backref='cliente',  lazy='dynamic')
    carrito   = db.relationship('ItemCarrito', backref='usuario',  lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def total_pedidos(self):
        return self.pedidos.count()

    def __repr__(self):
        return f'<Usuario {self.email}>'
