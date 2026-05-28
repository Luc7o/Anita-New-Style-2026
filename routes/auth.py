from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app_extensions import db
from models.usuario import Usuario
from forms.auth_forms import FormLogin, FormRegistro, Form2FA, FormOlvidePassword, FormRestablecerPassword
from utils.email_2fa import enviar_codigo_2fa, enviar_recuperacion_password

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))

    form = FormLogin()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data.lower()).first()

        if not usuario or not usuario.activo:
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html', form=form)

        if not usuario.check_password(form.password.data):
            flash('Correo o contraseña incorrectos.', 'danger')
            return render_template('auth/login.html', form=form)

        # ── Credenciales correctas → generar y enviar código 2FA ─────────────
        enviado = enviar_codigo_2fa(usuario)
        db.session.commit()  # guarda el código generado en BD

        # Guardamos en sesión el ID y si debe recordarse
        session['2fa_usuario_id'] = usuario.id
        session['2fa_recordar']   = form.recordar.data

        if enviado:
            flash(f'Te enviamos un código de 6 dígitos a {usuario.email}', 'info')
        else:
            flash('Hubo un problema al enviar el correo. Intenta de nuevo.', 'warning')

        return redirect(url_for('auth.verificar_2fa'))

    return render_template('auth/login.html', form=form)


@bp.route('/verificar-2fa', methods=['GET', 'POST'])
def verificar_2fa():
    # Si no hay sesión de 2FA pendiente, volver al login
    usuario_id = session.get('2fa_usuario_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        session.pop('2fa_usuario_id', None)
        return redirect(url_for('auth.login'))

    form = Form2FA()
    if form.validate_on_submit():
        if usuario.verificar_codigo_2fa(form.codigo.data):
            # ── Código correcto ────────────────────────────────────────────
            usuario.limpiar_codigo_2fa()
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()

            recordar = session.pop('2fa_recordar', False)
            session.pop('2fa_usuario_id', None)

            login_user(usuario, remember=recordar)

            next_page = request.args.get('next')
            flash(f'¡Bienvenida, {usuario.nombre}! 💖', 'success')
            return redirect(next_page or url_for('tienda.inicio'))
        else:
            flash('Código incorrecto o expirado. Intenta de nuevo.', 'danger')

    # Enmascarar el correo: lucio****@gmail.com
    partes     = usuario.email.split('@')
    email_mask = partes[0][:3] + '****@' + partes[1] if len(partes) == 2 else usuario.email

    return render_template('auth/verificar_2fa.html',
                           form=form, email_mask=email_mask,
                           usuario_id=usuario_id)


@bp.route('/verificar-2fa/reenviar', methods=['POST'])
def reenviar_codigo():
    usuario_id = session.get('2fa_usuario_id')
    if not usuario_id:
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return redirect(url_for('auth.login'))

    enviado = enviar_codigo_2fa(usuario)
    db.session.commit()

    if enviado:
        flash('Código reenviado a tu correo.', 'info')
    else:
        flash('No se pudo reenviar el código. Intenta más tarde.', 'danger')

    return redirect(url_for('auth.verificar_2fa'))


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))

    form = FormRegistro()
    if form.validate_on_submit():
        u = Usuario(
            nombre   = form.nombre.data.strip(),
            apellido = form.apellido.data.strip(),
            email    = form.email.data.lower().strip(),
            telefono = form.telefono.data,
        )
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash('¡Cuenta creada exitosamente! Bienvenida a Anita New Style. 🛍️', 'success')
        return redirect(url_for('tienda.inicio'))

    return render_template('auth/registro.html', form=form)


@bp.route('/olvide-password', methods=['GET', 'POST'])
def olvide_password():
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))

    form = FormOlvidePassword()
    enviado = False
    email_enviado = None

    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        usuario = Usuario.query.filter_by(email=email).first()
        email_enviado = email
        enviado = True
        # Enviamos el correo solo si el usuario existe (pero no revelamos si existe o no)
        if usuario:
            token = usuario.generar_token_reset_password()
            db.session.commit()
            enviar_recuperacion_password(usuario, token)

    return render_template('auth/olvide_password.html', form=form,
                           enviado=enviado, email_enviado=email_enviado)


@bp.route('/restablecer-password/<token>', methods=['GET', 'POST'])
def restablecer_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))

    usuario = Usuario.verificar_token_reset_password(token)
    if not usuario:
        flash('El enlace no es válido o ha expirado. Solicita uno nuevo.', 'danger')
        return redirect(url_for('auth.olvide_password'))

    form = FormRestablecerPassword()
    if form.validate_on_submit():
        usuario.set_password(form.password.data)
        usuario.limpiar_token_reset_password()
        db.session.commit()
        flash('¡Contraseña actualizada correctamente! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/restablecer_password.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('tienda.inicio'))
