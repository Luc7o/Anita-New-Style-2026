from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, RadioField
from wtforms.validators import DataRequired, Optional, Length

class FormCheckout(FlaskForm):
    nombre    = StringField('Nombre completo', validators=[DataRequired()])
    telefono  = StringField('Teléfono', validators=[DataRequired(), Length(7, 20)])
    tipo_entrega = RadioField('Tipo de entrega',
        choices=[('delivery','Delivery a domicilio'), ('recojo','Recoger en tienda')],
        default='delivery')
    direccion  = StringField('Dirección', validators=[Optional()])
    distrito   = StringField('Distrito',  validators=[Optional()])
    provincia  = StringField('Provincia', validators=[Optional()])
    departamento = StringField('Departamento', validators=[Optional()])
    referencia = StringField('Referencia', validators=[Optional()])
    metodo_pago = RadioField('Método de pago',
        choices=[
            ('yape',     'Yape'),
            ('tarjeta',  'Tarjeta de crédito/débito'),
            ('efectivo', 'Efectivo contra entrega'),
            ('recojo',   'Pago al recoger en tienda'),
        ], default='yape')
    nota      = TextAreaField('Nota del pedido', validators=[Optional(), Length(max=500)])
    submit    = SubmitField('Confirmar pedido')

class FormPerfil(FlaskForm):
    nombre       = StringField('Nombre', validators=[DataRequired()])
    apellido     = StringField('Apellido', validators=[DataRequired()])
    telefono     = StringField('Teléfono')
    dni          = StringField('DNI')
    direccion    = StringField('Dirección')
    distrito     = StringField('Distrito')
    provincia    = StringField('Provincia')
    departamento = StringField('Departamento')
    referencia   = StringField('Referencia')
    submit       = SubmitField('Guardar cambios')
