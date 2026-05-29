from datetime import datetime, timedelta
import random
from app_extensions import db


class Codigo2FA(db.Model):
    __tablename__ = 'codigos_2fa'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    codigo      = db.Column(db.String(6), nullable=False)
    expira_en   = db.Column(db.DateTime, nullable=False)
    usado       = db.Column(db.Boolean, default=False, nullable=False)
    creado_en   = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación inversa (opcional, para acceder desde usuario.codigos_2fa)
    usuario = db.relationship('Usuario', backref=db.backref('codigos_2fa', lazy='dynamic',
                                                             cascade='all, delete-orphan',
                                                             passive_deletes=True))

    # ── Métodos de clase (lógica centralizada aquí) ───────────────────────────

    @classmethod
    def generar(cls, usuario_id):
        """Crea y guarda un nuevo código de 6 dígitos válido por 10 minutos.
        Invalida cualquier código anterior del mismo usuario."""
        # Marcar los anteriores como usados
        cls.query.filter_by(usuario_id=usuario_id, usado=False).update({'usado': True})

        nuevo = cls(
            usuario_id=usuario_id,
            codigo=str(random.randint(100000, 999999)),
            expira_en=datetime.utcnow() + timedelta(minutes=10),
        )
        db.session.add(nuevo)
        return nuevo  # el llamador debe hacer db.session.commit()

    @classmethod
    def verificar(cls, usuario_id, codigo_ingresado):
        """Devuelve True si existe un código válido, no usado y no expirado."""
        registro = cls.query.filter_by(
            usuario_id=usuario_id,
            codigo=str(codigo_ingresado).strip(),
            usado=False,
        ).first()

        if not registro:
            return False
        if datetime.utcnow() > registro.expira_en:
            return False
        return True

    @classmethod
    def consumir(cls, usuario_id, codigo_ingresado):
        """Marca el código como usado. Llamar solo si verificar() devolvió True."""
        cls.query.filter_by(
            usuario_id=usuario_id,
            codigo=str(codigo_ingresado).strip(),
            usado=False,
        ).update({'usado': True})

    def __repr__(self):
        return f'<Codigo2FA usuario={self.usuario_id} usado={self.usado}>'
