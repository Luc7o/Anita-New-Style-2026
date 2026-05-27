from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, IntegerField, DecimalField,
                     SelectField, BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional, NumberRange, Length, Email


# ── Producto completo (admin integrado) ────────────────────────────────────────
class FormProductoAlmacen(FlaskForm):
    nombre        = StringField('Nombre del producto', validators=[DataRequired(), Length(max=150)])
    descripcion   = TextAreaField('Descripción', validators=[Optional()])
    sku           = StringField('SKU / Código interno', validators=[Optional(), Length(max=60)])
    codigo_barras = StringField('Código de barras', validators=[Optional(), Length(max=100)])
    categoria_id  = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    proveedor_id  = SelectField('Proveedor', coerce=int, validators=[Optional()])
    precio_compra = DecimalField('Precio de compra (S/)', places=2, validators=[Optional()], default=0)
    precio        = DecimalField('Precio de venta (S/)', places=2,
                                 validators=[DataRequired(), NumberRange(min=0.01)])
    precio_oferta = DecimalField('Precio oferta (S/)', places=2,
                                 validators=[Optional(), NumberRange(min=0)])
    stock         = IntegerField('Stock inicial', validators=[Optional(), NumberRange(min=0)], default=0)
    stock_minimo  = IntegerField('Stock mínimo (alerta)', validators=[Optional(), NumberRange(min=0)], default=5)
    tallas        = StringField('Tallas (separadas por coma)', validators=[Optional()])
    colores       = StringField('Colores (separados por coma)', validators=[Optional()])
    unidad        = SelectField('Unidad de medida',
                                choices=[('unidad','Unidad'),('par','Par'),('caja','Caja'),
                                         ('docena','Docena'),('kg','Kilogramo'),('m','Metro')],
                                default='unidad')
    imagen        = FileField('Imagen del producto',
                              validators=[Optional(), FileAllowed(['jpg','jpeg','png','webp'])])
    destacado     = BooleanField('Producto destacado')
    es_nuevo      = BooleanField('Es nuevo', default=True)
    activo        = BooleanField('Activo', default=True)
    submit        = SubmitField('Guardar')


# ── Proveedores ────────────────────────────────────────────────────────────────
class FormProveedor(FlaskForm):
    nombre    = StringField('Razón social / Nombre', validators=[DataRequired(), Length(max=150)])
    ruc       = StringField('RUC', validators=[Optional(), Length(max=11)])
    contacto  = StringField('Persona de contacto', validators=[Optional(), Length(max=100)])
    telefono  = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    email     = StringField('Email', validators=[Optional(), Email(), Length(max=150)])
    direccion = StringField('Dirección', validators=[Optional(), Length(max=250)])
    notas     = TextAreaField('Notas', validators=[Optional()])
    activo    = BooleanField('Activo', default=True)
    submit    = SubmitField('Guardar')


# ── Movimiento de stock ────────────────────────────────────────────────────────
class FormMovimiento(FlaskForm):
    producto_id  = SelectField('Producto', coerce=int, validators=[DataRequired()])
    tipo         = SelectField('Tipo de movimiento',
                               choices=[('entrada','Entrada de mercadería'),
                                        ('salida', 'Salida / Retiro'),
                                        ('ajuste', 'Ajuste de inventario'),
                                        ('devolucion','Devolución de cliente')],
                               validators=[DataRequired()])
    cantidad     = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    motivo       = StringField('Motivo / Descripción', validators=[Optional(), Length(max=250)])
    referencia   = StringField('N° Factura / Referencia', validators=[Optional(), Length(max=100)])
    proveedor_id = SelectField('Proveedor (opcional)', coerce=int, validators=[Optional()])
    submit       = SubmitField('Registrar movimiento')


# ── Venta física ───────────────────────────────────────────────────────────────
class FormVenta(FlaskForm):
    cliente_nombre = StringField('Nombre del cliente', validators=[Optional(), Length(max=150)])
    cliente_doc    = StringField('DNI / RUC', validators=[Optional(), Length(max=15)])
    metodo_pago    = SelectField('Método de pago',
                                 choices=[('efectivo','Efectivo'),
                                          ('yape','Yape / Plin'),
                                          ('tarjeta','Tarjeta'),
                                          ('transferencia','Transferencia')],
                                 validators=[DataRequired()])
    descuento      = DecimalField('Descuento (S/)', places=2, validators=[Optional()], default=0)
    notas          = TextAreaField('Notas', validators=[Optional()])
    submit         = SubmitField('Registrar venta')
