from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app_extensions import db
from models.carrito  import ItemCarrito
from models.producto import Producto

bp = Blueprint('carrito', __name__)


@bp.route('/')
@login_required
def ver_carrito():
    items       = ItemCarrito.query.filter_by(usuario_id=current_user.id).all()
    subtotal    = sum(i.subtotal for i in items)
    costo_envio = 0 if subtotal >= current_app.config['ENVIO_GRATIS_DESDE'] else current_app.config['COSTO_ENVIO']
    total       = subtotal + costo_envio
    return render_template('carrito/carrito.html',
                           items=items, subtotal=subtotal,
                           costo_envio=costo_envio, total=total)


@bp.route('/agregar/<int:producto_id>', methods=['POST'])
@login_required
def agregar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    cantidad = int(request.form.get('cantidad', 1))
    talla    = request.form.get('talla', '')
    color    = request.form.get('color', '')

    def _ajax_error(msg):
        return jsonify({'ok': False, 'msg': msg}), 400

    def _flash_error(msg):
        flash(msg, 'warning')
        return redirect(request.referrer or url_for('tienda.inicio'))

    es_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # ── FIX: Validar que el producto esté activo y con stock ────────────────
    if not producto.activo:
        msg = f'"{producto.nombre}" ya no está disponible.'
        return _ajax_error(msg) if es_ajax else _flash_error(msg)

    if producto.sin_stock:
        msg = f'"{producto.nombre}" está agotado.'
        return _ajax_error(msg) if es_ajax else _flash_error(msg)

    # Calcular cantidad total resultante (ya en carrito + nueva)
    item_existente = ItemCarrito.query.filter_by(
        usuario_id=current_user.id, producto_id=producto_id,
        talla=talla, color=color
    ).first()

    cantidad_en_carrito = item_existente.cantidad if item_existente else 0
    cantidad_total      = cantidad_en_carrito + cantidad

    if cantidad_total > producto.stock:
        disponible = producto.stock - cantidad_en_carrito
        if disponible <= 0:
            msg = f'Ya tienes el máximo disponible de "{producto.nombre}" en tu carrito ({producto.stock} unidad(es)).'
        else:
            msg = (f'Solo puedes agregar {disponible} unidad(es) más de "{producto.nombre}" '
                   f'(stock disponible: {producto.stock}).')
        return _ajax_error(msg) if es_ajax else _flash_error(msg)

    # ── Agregar o actualizar item ────────────────────────────────────────────
    if item_existente:
        item_existente.cantidad = cantidad_total
    else:
        item = ItemCarrito(
            usuario_id=current_user.id, producto_id=producto_id,
            cantidad=cantidad, talla=talla, color=color,
        )
        db.session.add(item)
    db.session.commit()

    if es_ajax:
        cant_total = ItemCarrito.query.filter_by(usuario_id=current_user.id).count()
        return jsonify({'ok': True, 'cant_carrito': cant_total})

    flash(f'"{producto.nombre}" agregado al carrito. 🛍️', 'success')
    return redirect(request.referrer or url_for('tienda.inicio'))


@bp.route('/actualizar/<int:item_id>', methods=['POST'])
@login_required
def actualizar(item_id):
    item     = ItemCarrito.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()
    cantidad = int(request.form.get('cantidad', 1))

    if cantidad < 1:
        db.session.delete(item)
    else:
        # ── FIX: Validar stock antes de actualizar ───────────────────────────
        if cantidad > item.producto.stock:
            flash(
                f'Solo hay {item.producto.stock} unidad(es) disponibles de '
                f'"{item.producto.nombre}". Se ajustó la cantidad.',
                'warning',
            )
            cantidad = item.producto.stock   # ajustar al máximo disponible
            if cantidad < 1:
                db.session.delete(item)
                db.session.commit()
                return redirect(url_for('carrito.ver_carrito'))
        item.cantidad = cantidad

    db.session.commit()
    return redirect(url_for('carrito.ver_carrito'))


@bp.route('/eliminar/<int:item_id>', methods=['POST'])
@login_required
def eliminar(item_id):
    item = ItemCarrito.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Producto eliminado del carrito.', 'info')
    return redirect(url_for('carrito.ver_carrito'))


@bp.route('/vaciar', methods=['POST'])
@login_required
def vaciar():
    ItemCarrito.query.filter_by(usuario_id=current_user.id).delete()
    db.session.commit()
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('carrito.ver_carrito'))
