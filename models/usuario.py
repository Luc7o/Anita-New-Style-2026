from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app_extensions import db
import secrets


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id             = db.Column(db.Integer, primary_key=True)
    nombre         = db.Column(db.String(80),  nullable=False)
    apellido       = db.Column(db.String(80),  nullable=False)
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

    # ── 2FA por correo ────────────────────────────────────────────────────────
    codigo_2fa        = db.Column(db.String(6))
    codigo_2fa_expira = db.Column(db.DateTime)

    # ── Recuperación de contraseña ────────────────────────────────────────────
    reset_token        = db.Column(db.String(100), unique=True, index=True)
    reset_token_expira = db.Column(db.DateTime)

    # Relaciones
    pedidos = db.relationship('Pedido',      backref='cliente', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True)
    carrito = db.relationship('ItemCarrito', backref='usuario', lazy='dynamic',
                              cascade='all, delete-orphan', passive_deletes=True)

    # ── Contraseña ────────────────────────────────────────────────────────────
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ── 2FA ───────────────────────────────────────────────────────────────────
    def generar_codigo_2fa(self):
        """Genera un código de 6 dígitos válido por 10 minutos."""
        import random
        from datetime import timedelta
        self.codigo_2fa        = str(random.randint(100000, 999999))
        self.codigo_2fa_expira = datetime.utcnow() + timedelta(minutes=10)
        return self.codigo_2fa

    def verificar_codigo_2fa(self, codigo):
        """Devuelve True si el código es correcto y no expiró."""
        if not self.codigo_2fa or not self.codigo_2fa_expira:
            return False
        if datetime.utcnow() > self.codigo_2fa_expira:
            return False
        return self.codigo_2fa == str(codigo).strip()

    def limpiar_codigo_2fa(self):
        """Invalida el código después de usarlo."""
        self.codigo_2fa        = None
        self.codigo_2fa_expira = None

    # ── Recuperación de contraseña ────────────────────────────────────────────
    def generar_token_reset_password(self):
        """Genera un token seguro válido por 30 minutos."""
        from datetime import timedelta
        self.reset_token        = secrets.token_urlsafe(48)
        self.reset_token_expira = datetime.utcnow() + timedelta(minutes=30)
        return self.reset_token

    def limpiar_token_reset_password(self):
        """Invalida el token después de usarlo."""
        self.reset_token        = None
        self.reset_token_expira = None

    @staticmethod
    def verificar_token_reset_password(token):
        """Busca el usuario por token y verifica que no haya expirado."""
        usuario = Usuario.query.filter_by(reset_token=token).first()
        if not usuario or not usuario.reset_token_expira:
            return None
        if datetime.utcnow() > usuario.reset_token_expira:
            return None
        return usuario

    # ── Propiedades ───────────────────────────────────────────────────────────
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def total_pedidos(self):
        return self.pedidos.count()

    def __repr__(self):
        return f'<Usuario {self.email}>'
