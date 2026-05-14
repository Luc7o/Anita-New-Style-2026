from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app_extensions import db
from models.usuario import Usuario
from forms.auth_forms import FormLogin, FormRegistro

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))
    form = FormLogin()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data.lower()).first()
        if usuario and usuario.activo and usuario.check_password(form.password.data):
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()
            login_user(usuario, remember=form.recordar.data)
            next_page = request.args.get('next')
            flash(f'¡Bienvenida, {usuario.nombre}! 💖', 'success')
            return redirect(next_page or url_for('tienda.inicio'))
        flash('Correo o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html', form=form)

@bp.route('/registro', methods=['GET','POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('tienda.inicio'))
    form = FormRegistro()
    if form.validate_on_submit():
        u = Usuario(
            nombre=form.nombre.data.strip(),
            apellido=form.apellido.data.strip(),
            email=form.email.data.lower().strip(),
            telefono=form.telefono.data,
        )
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        flash('¡Cuenta creada exitosamente! Bienvenida a Anita New Style. 🛍️', 'success')
        return redirect(url_for('tienda.inicio'))
    return render_template('auth/registro.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('tienda.inicio'))
