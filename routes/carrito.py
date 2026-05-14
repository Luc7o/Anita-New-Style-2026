from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app_extensions import db
from models.carrito  import ItemCarrito
from models.producto import Producto

bp = Blueprint('carrito', __name__)

@bp.route('/')
@login_required
def ver_carrito():
    items = ItemCarrito.query.filter_by(usuario_id=current_user.id).all()
    subtotal = sum(i.subtotal for i in items)
    from flask import current_app
    costo_envio = 0 if subtotal >= current_app.config['ENVIO_GRATIS_DESDE'] else current_app.config['COSTO_ENVIO']
    total = subtotal + costo_envio
    return render_template('carrito/carrito.html', items=items, subtotal=subtotal, costo_envio=costo_envio, total=total)

@bp.route('/agregar/<int:producto_id>', methods=['POST'])
@login_required
def agregar(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    cantidad = int(request.form.get('cantidad', 1))
    talla    = request.form.get('talla', '')
    color    = request.form.get('color', '')

    item = ItemCarrito.query.filter_by(
        usuario_id=current_user.id, producto_id=producto_id,
        talla=talla, color=color
    ).first()

    if item:
        item.cantidad += cantidad
    else:
        item = ItemCarrito(usuario_id=current_user.id, producto_id=producto_id,
                           cantidad=cantidad, talla=talla, color=color)
        db.session.add(item)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cant = ItemCarrito.query.filter_by(usuario_id=current_user.id).count()
        return jsonify({'ok': True, 'cant_carrito': cant})
    flash(f'"{producto.nombre}" agregado al carrito. 🛍️', 'success')
    return redirect(request.referrer or url_for('tienda.inicio'))

@bp.route('/actualizar/<int:item_id>', methods=['POST'])
@login_required
def actualizar(item_id):
    item = ItemCarrito.query.filter_by(id=item_id, usuario_id=current_user.id).first_or_404()
    cantidad = int(request.form.get('cantidad', 1))
    if cantidad < 1:
        db.session.delete(item)
    else:
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
