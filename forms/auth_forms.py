from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models.usuario import Usuario
from utils.seguridad import validar_contrasena_fuerte


class FormLogin(FlaskForm):
    email           = StringField('Correo electrónico', validators=[
                          DataRequired(message='Requerido'),
                          Email(message='Correo inválido')
                      ])
    password        = PasswordField('Contraseña', validators=[DataRequired(message='Requerido')])
    recordar        = BooleanField('Recordarme')
    submit          = SubmitField('Ingresar')


class FormRegistro(FlaskForm):
    nombre    = StringField('Nombre',    validators=[DataRequired(), Length(2, 80)])
    apellido  = StringField('Apellido',  validators=[DataRequired(), Length(2, 80)])
    email     = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    telefono  = StringField('Teléfono',  validators=[Length(0, 20)])
    password  = PasswordField('Contraseña', validators=[DataRequired(), Length(8, 128,
                    message='Mínimo 8 caracteres.')])
    password2 = PasswordField('Confirmar contraseña', validators=[
                    DataRequired(),
                    EqualTo('password', message='Las contraseñas no coinciden.')
                ])
    submit    = SubmitField('Crear cuenta')

    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Este correo ya está registrado.')

    def validate_password(self, field):
        """Aplica las reglas de contraseña fuerte."""
        errores = validar_contrasena_fuerte(field.data)
        if errores:
            raise ValidationError(' '.join(errores))


class FormCambiarPassword(FlaskForm):
    password_actual   = PasswordField('Contraseña actual',   validators=[DataRequired()])
    password_nueva    = PasswordField('Nueva contraseña',    validators=[
                            DataRequired(),
                            Length(8, 128, message='Mínimo 8 caracteres.')
                        ])
    password_confirma = PasswordField('Confirmar contraseña', validators=[
                            DataRequired(),
                            EqualTo('password_nueva', message='Las contraseñas no coinciden.')
                        ])
    submit = SubmitField('Actualizar contraseña')

    def validate_password_nueva(self, field):
        errores = validar_contrasena_fuerte(field.data)
        if errores:
            raise ValidationError(' '.join(errores))


class Form2FA(FlaskForm):
    """Formulario para ingresar el código de doble factor."""
    codigo = StringField('Código de verificación', validators=[
                 DataRequired(message='Ingresa el código.'),
                 Length(6, 6, message='El código tiene 6 dígitos.')
             ])
    submit = SubmitField('Verificar')


class FormOlvidePassword(FlaskForm):
    """Formulario para solicitar recuperación de contraseña."""
    email  = StringField('Correo electrónico', validators=[
                 DataRequired(message='Requerido'),
                 Email(message='Correo inválido')
             ])
    submit = SubmitField('Enviar instrucciones')


class FormRestablecerPassword(FlaskForm):
    """Formulario para establecer una nueva contraseña con token."""
    password  = PasswordField('Nueva contraseña', validators=[
                    DataRequired(),
                    Length(8, 128, message='Mínimo 8 caracteres.')
                ])
    password2 = PasswordField('Confirmar contraseña', validators=[
                    DataRequired(),
                    EqualTo('password', message='Las contraseñas no coinciden.')
                ])
    submit    = SubmitField('Guardar nueva contraseña')

    def validate_password(self, field):
        from utils.seguridad import validar_contrasena_fuerte
        errores = validar_contrasena_fuerte(field.data)
        if errores:
            raise ValidationError(' '.join(errores))
