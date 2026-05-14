from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

class FormProducto(FlaskForm):
    nombre        = StringField('Nombre del producto', validators=[DataRequired(), ])
    descripcion   = TextAreaField('Descripción')
    precio        = DecimalField('Precio (S/)', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    precio_oferta = DecimalField('Precio oferta (S/)', validators=[Optional(), NumberRange(min=0)], places=2)
    categoria_id  = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    tallas        = StringField('Tallas (separadas por coma)')
    colores       = StringField('Colores (separados por coma)')
    stock         = IntegerField('Stock', validators=[NumberRange(min=0)], default=0)
    sku           = StringField('SKU / Código')
    destacado     = BooleanField('Producto destacado')
    es_nuevo      = BooleanField('Es nuevo', default=True)
    activo        = BooleanField('Activo', default=True)
    imagen        = FileField('Imagen principal', validators=[FileAllowed(['jpg','jpeg','png','webp'], 'Solo imágenes')])
    submit        = SubmitField('Guardar producto')

class FormCategoria(FlaskForm):
    nombre      = StringField('Nombre', validators=[DataRequired()])
    slug        = StringField('Slug (URL)')
    descripcion = StringField('Descripción')
    icono       = StringField('Ícono')
    activo      = BooleanField('Activa', default=True)
    submit      = SubmitField('Guardar')
