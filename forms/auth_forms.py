from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models.usuario import Usuario

class FormLogin(FlaskForm):
    email    = StringField('Correo electrónico', validators=[DataRequired(message='Requerido'), Email(message='Correo inválido')])
    password = PasswordField('Contraseña', validators=[DataRequired(message='Requerido')])
    recordar = BooleanField('Recordarme')
    submit   = SubmitField('Ingresar')

class FormRegistro(FlaskForm):
    nombre   = StringField('Nombre', validators=[DataRequired(), Length(2, 80)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(2, 80)])
    email    = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[Length(0, 20)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(6, 50)])
    password2= PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden')])
    submit   = SubmitField('Crear cuenta')

    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Este correo ya está registrado.')

class FormCambiarPassword(FlaskForm):
    password_actual  = PasswordField('Contraseña actual', validators=[DataRequired()])
    password_nueva   = PasswordField('Nueva contraseña',  validators=[DataRequired(), Length(6, 50)])
    password_confirma= PasswordField('Confirmar contraseña', validators=[DataRequired(), EqualTo('password_nueva')])
    submit           = SubmitField('Actualizar contraseña')
