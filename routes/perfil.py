from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app_extensions import db
from forms.checkout_forms import FormPerfil
from forms.auth_forms import FormCambiarPassword

bp = Blueprint('perfil', __name__)

@bp.route('/')
@login_required
def perfil():
    return render_template('perfil/perfil.html')

@bp.route('/editar', methods=['GET','POST'])
@login_required
def editar():
    form = FormPerfil(obj=current_user)
    if form.validate_on_submit():
        current_user.nombre      = form.nombre.data
        current_user.apellido    = form.apellido.data
        current_user.telefono    = form.telefono.data
        current_user.dni         = form.dni.data
        current_user.direccion   = form.direccion.data
        current_user.distrito    = form.distrito.data
        current_user.provincia   = form.provincia.data
        current_user.departamento= form.departamento.data
        current_user.referencia  = form.referencia.data
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('perfil.perfil'))
    return render_template('perfil/editar.html', form=form)

@bp.route('/cambiar-password', methods=['GET','POST'])
@login_required
def cambiar_password():
    form = FormCambiarPassword()
    if form.validate_on_submit():
        if not current_user.check_password(form.password_actual.data):
            flash('La contraseña actual es incorrecta.', 'danger')
        else:
            current_user.set_password(form.password_nueva.data)
            db.session.commit()
            flash('Contraseña actualizada.', 'success')
            return redirect(url_for('perfil.perfil'))
    return render_template('perfil/cambiar_password.html', form=form)
