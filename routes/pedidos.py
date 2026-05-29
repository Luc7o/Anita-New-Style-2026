from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app_extensions import db, csrf
from models.carrito  import ItemCarrito
from models.pedido   import Pedido, DetallePedido
from models.producto import Producto
from models.movimiento import MovimientoStock
from forms.checkout_forms import FormCheckout
import stripe

bp = Blueprint('pedidos', __name__)

def _calcular_carrito(usuario_id):
    items    = ItemCarrito.query.filter_by(usuario_id=usuario_id).all()
    subtotal = sum(i.subtotal for i in items)
    envio    = 0 if subtotal >= current_app.config['ENVIO_GRATIS_DESDE'] else current_app.config['COSTO_ENVIO']
    return items, subtotal, envio, subtotal + envio


def _render_checkout(form, items, subtotal, costo_envio, total):
    """Helper para no repetir el render_template en múltiples return."""
    return render_template(
        'checkout/checkout.html', form=form, items=items,
        subtotal=subtotal, costo_envio=costo_envio, total=total,
        STRIPE_PUBLIC_KEY=current_app.config['STRIPE_PUBLIC_KEY'],
        YAPE_NUMERO=current_app.config['YAPE_NUMERO'],
        YAPE_NOMBRE=current_app.config['YAPE_NOMBRE'],
    )


@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items, subtotal, costo_envio, total = _calcular_carrito(current_user.id)
    if not items:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('tienda.inicio'))

    form = FormCheckout()

    # ── Prellenar con datos del perfil (solo GET) ───────────────────────────
    if request.method == 'GET':
        form.nombre.data       = current_user.nombre_completo
        form.telefono.data     = current_user.telefono or ''
        form.direccion.data    = current_user.direccion or ''
        form.distrito.data     = current_user.distrito or ''
        form.provincia.data    = current_user.provincia or ''
        form.departamento.data = current_user.departamento or ''

    if form.validate_on_submit():
        tipo_entrega = form.tipo_entrega.data
        metodo_pago  = form.metodo_pago.data

        # ── FIX 1: "Pago al recoger" implica recojo en tienda ──────────────
        if metodo_pago == 'recojo':
            tipo_entrega = 'recojo'

        # ── FIX 2: Delivery requiere dirección completa (server-side) ──────
        if tipo_entrega == 'delivery':
            campos_dir = [
                (form.direccion.data,    'La dirección es requerida para delivery.'),
                (form.distrito.data,     'El distrito es requerido para delivery.'),
                (form.provincia.data,    'La provincia es requerida para delivery.'),
                (form.departamento.data, 'El departamento es requerido para delivery.'),
            ]
            errores_dir = [msg for val, msg in campos_dir if not (val and val.strip())]
            if errores_dir:
                for msg in errores_dir:
                    flash(msg, 'danger')
                return _render_checkout(form, items, subtotal, costo_envio, total)

        # ── FIX 3: Recojo en tienda no cobra envío ──────────────────────────
        if tipo_entrega == 'recojo':
            costo_envio = 0
            total = subtotal

        # ── FIX 4: Validar stock disponible ANTES de crear el pedido ────────
        sin_stock = [
            f'"{i.producto.nombre}" solo tiene {i.producto.stock} unidad(es) disponibles '
            f'(solicitaste {i.cantidad}).'
            for i in items if i.producto.stock < i.cantidad
        ]
        agotados = [
            f'"{i.producto.nombre}" está agotado y no puede agregarse al pedido.'
            for i in items if i.producto.sin_stock
        ]
        errores_stock = agotados + sin_stock
        if errores_stock:
            for msg in errores_stock:
                flash(msg, 'danger')
            return _render_checkout(form, items, subtotal, costo_envio, total)

        # ── Crear pedido ────────────────────────────────────────────────────
        pedido = Pedido(
            numero_pedido    = Pedido.generar_numero(),
            usuario_id       = current_user.id,
            metodo_pago      = metodo_pago,
            tipo_entrega     = tipo_entrega,
            subtotal         = subtotal,
            costo_envio      = costo_envio,
            total            = total,
            envio_nombre     = form.nombre.data,
            envio_telefono   = form.telefono.data,
            envio_direccion  = form.direccion.data  if tipo_entrega == 'delivery' else '',
            envio_distrito   = form.distrito.data   if tipo_entrega == 'delivery' else '',
            envio_provincia  = form.provincia.data  if tipo_entrega == 'delivery' else '',
            envio_dpto       = form.departamento.data if tipo_entrega == 'delivery' else '',
            envio_referencia = form.referencia.data,
            nota             = form.nota.data,
        )
        db.session.add(pedido)
        db.session.flush()   # obtener pedido.id antes de los detalles

        # ── FIX 5: Descontar stock + registrar MovimientoStock ──────────────
        for item in items:
            stock_antes   = item.producto.stock
            stock_despues = stock_antes - item.cantidad

            det = DetallePedido(
                pedido_id   = pedido.id,
                producto_id = item.producto_id,
                cantidad    = item.cantidad,
                precio_unit = item.producto.precio_final,
                talla       = item.talla,
                color       = item.color,
                subtotal    = item.subtotal,
            )
            db.session.add(det)

            # Actualizar stock y vendidos
            item.producto.stock    = stock_despues
            item.producto.vendidos = (item.producto.vendidos or 0) + item.cantidad

            # Movimiento de inventario (trazabilidad)
            mov = MovimientoStock(
                producto_id   = item.producto_id,
                tipo          = 'venta',
                cantidad      = item.cantidad,
                stock_antes   = stock_antes,
                stock_despues = stock_despues,
                motivo        = f'Venta online {pedido.numero_pedido}',
                referencia    = pedido.numero_pedido,
                usuario_id    = current_user.id,
            )
            db.session.add(mov)

        # Vaciar carrito y persistir todo
        ItemCarrito.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()

        # ── Redirigir según método de pago ──────────────────────────────────
        if metodo_pago == 'tarjeta':
            return redirect(url_for('pedidos.pagar_tarjeta', numero=pedido.numero_pedido))
        elif metodo_pago == 'yape':
            return redirect(url_for('pedidos.pagar_yape', numero=pedido.numero_pedido))
        else:
            flash(f'¡Pedido #{pedido.numero_pedido} confirmado! 🎉', 'success')
            return redirect(url_for('pedidos.confirmacion', numero=pedido.numero_pedido))

    return _render_checkout(form, items, subtotal, costo_envio, total)


# ── Yape ────────────────────────────────────────────────────────────────────

@bp.route('/pagar/yape/<numero>')
@login_required
def pagar_yape(numero):
    pedido = Pedido.query.filter_by(
        numero_pedido=numero, usuario_id=current_user.id
    ).first_or_404()
    return render_template(
        'checkout/pago_yape.html', pedido=pedido,
        YAPE_NUMERO=current_app.config['YAPE_NUMERO'],
        YAPE_NOMBRE=current_app.config['YAPE_NOMBRE'],
    )


@bp.route('/pagar/yape/<numero>/confirmar', methods=['POST'])
@login_required
def confirmar_yape(numero):
    pedido = Pedido.query.filter_by(
        numero_pedido=numero, usuario_id=current_user.id
    ).first_or_404()

    # ── FIX 6: Guard contra doble confirmación ──────────────────────────────
    if pedido.estado_pago == 'pagado':
        flash('Este pedido ya fue confirmado anteriormente. ✅', 'info')
        return redirect(url_for('pedidos.confirmacion', numero=numero))
    if pedido.estado in ('cancelado',):
        flash('Este pedido está cancelado y no puede confirmarse.', 'danger')
        return redirect(url_for('pedidos.mis_pedidos'))

    # Subir comprobante si se adjuntó
    if 'comprobante' in request.files:
        f = request.files['comprobante']
        if f and f.filename:
            import os, uuid
            from werkzeug.utils import secure_filename
            ext    = f.filename.rsplit('.', 1)[-1].lower()
            nombre = f"yape_{uuid.uuid4().hex[:8]}.{ext}"
            ruta   = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre)
            f.save(ruta)
            pedido.comprobante_yape = nombre

    pedido.estado_pago = 'pendiente'   # pendiente de verificación manual
    pedido.estado      = 'confirmado'
    db.session.commit()
    flash('¡Pago por Yape registrado! Verificaremos tu voucher en breve. 💚', 'success')
    return redirect(url_for('pedidos.confirmacion', numero=numero))


# ── Tarjeta (Stripe) ────────────────────────────────────────────────────────

@bp.route('/pagar/tarjeta/<numero>', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def pagar_tarjeta(numero):
    pedido = Pedido.query.filter_by(
        numero_pedido=numero, usuario_id=current_user.id
    ).first_or_404()

    if request.method == 'POST':
        # Guard: ya pagado con tarjeta
        if pedido.estado_pago == 'pagado':
            return jsonify({'error': 'Este pedido ya fue pagado.'}), 400

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        try:
            intent = stripe.PaymentIntent.create(
                amount   = int(float(pedido.total) * 100),
                currency = 'pen',
                metadata = {'pedido_id': pedido.id, 'numero': pedido.numero_pedido},
            )
            pedido.stripe_id = intent.id
            db.session.commit()
            return jsonify({'client_secret': intent.client_secret})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return render_template(
        'checkout/pago_tarjeta.html', pedido=pedido,
        STRIPE_PUBLIC_KEY=current_app.config['STRIPE_PUBLIC_KEY'],
    )


@bp.route('/stripe/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    payload    = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET']
        )
    except Exception:
        return '', 400

    if event['type'] == 'payment_intent.succeeded':
        pi     = event['data']['object']
        pedido = Pedido.query.filter_by(stripe_id=pi['id']).first()
        if pedido and pedido.estado_pago != 'pagado':
            pedido.estado_pago = 'pagado'
            pedido.estado      = 'confirmado'
            db.session.commit()

    return '', 200


# ── Confirmación y listado ──────────────────────────────────────────────────

@bp.route('/confirmacion/<numero>')
@login_required
def confirmacion(numero):
    pedido = Pedido.query.filter_by(
        numero_pedido=numero, usuario_id=current_user.id
    ).first_or_404()
    return render_template('checkout/confirmacion.html', pedido=pedido)


@bp.route('/mis-pedidos')
@login_required
def mis_pedidos():
    pagina  = request.args.get('pagina', 1, type=int)
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id)\
                    .order_by(Pedido.fecha_creacion.desc())\
                    .paginate(page=pagina, per_page=10, error_out=False)
    return render_template('perfil/mis_pedidos.html', pedidos=pedidos)


@bp.route('/pedido/<numero>')
@login_required
def detalle_pedido(numero):
    pedido = Pedido.query.filter_by(
        numero_pedido=numero, usuario_id=current_user.id
    ).first_or_404()
    return render_template('perfil/detalle_pedido.html', pedido=pedido)
