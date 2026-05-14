from app_extensions import db

class ItemCarrito(db.Model):
    __tablename__ = 'carrito'

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad    = db.Column(db.Integer, nullable=False, default=1)
    talla       = db.Column(db.String(20))
    color       = db.Column(db.String(50))

    @property
    def subtotal(self):
        return self.producto.precio_final * self.cantidad

    def __repr__(self):
        return f'<ItemCarrito usuario={self.usuario_id} prod={self.producto_id}>'
