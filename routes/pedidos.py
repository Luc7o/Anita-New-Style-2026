from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app_extensions import db, csrf
from models.carrito  import ItemCarrito
from models.pedido   import Pedido, DetallePedido
from models.producto import Producto
from forms.checkout_forms import FormCheckout
import stripe

bp = Blueprint('pedidos', __name__)

def _calcular_carrito(usuario_id):
    items    = ItemCarrito.query.filter_by(usuario_id=usuario_id).all()
    subtotal = sum(i.subtotal for i in items)
    envio    = 0 if subtotal >= current_app.config['ENVIO_GRATIS_DESDE'] else current_app.config['COSTO_ENVIO']
    return items, subtotal, envio, subtotal + envio

@bp.route('/checkout', methods=['GET','POST'])
@login_required
def checkout():
    items, subtotal, costo_envio, total = _calcular_carrito(current_user.id)
    if not items:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('tienda.inicio'))

    form = FormCheckout()
    # Prellenar con datos del perfil
    if request.method == 'GET':
        form.nombre.data    = current_user.nombre_completo
        form.telefono.data  = current_user.telefono or ''
        form.direccion.data = current_user.direccion or ''
        form.distrito.data  = current_user.distrito or ''
        form.provincia.data = current_user.provincia or ''
        form.departamento.data = current_user.departamento or ''

    if form.validate_on_submit():
        pedido = Pedido(
            numero_pedido  = Pedido.generar_numero(),
            usuario_id     = current_user.id,
            metodo_pago    = form.metodo_pago.data,
            tipo_entrega   = form.tipo_entrega.data,
            subtotal       = subtotal,
            costo_envio    = costo_envio,
            total          = total,
            envio_nombre   = form.nombre.data,
            envio_telefono = form.telefono.data,
            envio_direccion= form.direccion.data,
            envio_distrito = form.distrito.data,
            envio_provincia= form.provincia.data,
            envio_dpto     = form.departamento.data,
            envio_referencia = form.referencia.data,
            nota           = form.nota.data,
        )
        if form.metodo_pago.data in ('efectivo', 'recojo'):
            pedido.estado_pago = 'pendiente'

        db.session.add(pedido)
        db.session.flush()

        for item in items:
            det = DetallePedido(
                pedido_id   = pedido.id,
                producto_id = item.producto_id,
                cantidad    = item.cantidad,
                precio_unit = item.producto.precio_final,
                talla       = item.talla,
                color       = item.color,
                subtotal    = item.subtotal,
            )
            item.producto.stock    -= item.cantidad
            item.producto.vendidos += item.cantidad
            db.session.add(det)

        ItemCarrito.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()

        # Redirigir según método de pago
        if form.metodo_pago.data == 'tarjeta':
            return redirect(url_for('pedidos.pagar_tarjeta', numero=pedido.numero_pedido))
        elif form.metodo_pago.data == 'yape':
            return redirect(url_for('pedidos.pagar_yape', numero=pedido.numero_pedido))
        else:
            flash(f'¡Pedido #{pedido.numero_pedido} confirmado! 🎉', 'success')
            return redirect(url_for('pedidos.confirmacion', numero=pedido.numero_pedido))

    return render_template('checkout/checkout.html', form=form, items=items,
                           subtotal=subtotal, costo_envio=costo_envio, total=total,
                           STRIPE_PUBLIC_KEY=current_app.config['STRIPE_PUBLIC_KEY'],
                           YAPE_NUMERO=current_app.config['YAPE_NUMERO'],
                           YAPE_NOMBRE=current_app.config['YAPE_NOMBRE'])

@bp.route('/pagar/yape/<numero>')
@login_required
def pagar_yape(numero):
    pedido = Pedido.query.filter_by(numero_pedido=numero, usuario_id=current_user.id).first_or_404()
    return render_template('checkout/pago_yape.html', pedido=pedido,
                           YAPE_NUMERO=current_app.config['YAPE_NUMERO'],
                           YAPE_NOMBRE=current_app.config['YAPE_NOMBRE'])

@bp.route('/pagar/yape/<numero>/confirmar', methods=['POST'])
@login_required
def confirmar_yape(numero):
    pedido = Pedido.query.filter_by(numero_pedido=numero, usuario_id=current_user.id).first_or_404()
    # Subir comprobante si se adjuntó
    if 'comprobante' in request.files:
        f = request.files['comprobante']
        if f.filename:
            import os, uuid
            from werkzeug.utils import secure_filename
            ext  = f.filename.rsplit('.', 1)[-1].lower()
            nombre = f"yape_{uuid.uuid4().hex[:8]}.{ext}"
            ruta   = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre)
            f.save(ruta)
            pedido.comprobante_yape = nombre
    pedido.estado_pago = 'pendiente'
    pedido.estado      = 'confirmado'
    db.session.commit()
    flash('¡Pago por Yape registrado! Verificaremos tu voucher en breve. 💚', 'success')
    return redirect(url_for('pedidos.confirmacion', numero=numero))

@bp.route('/pagar/tarjeta/<numero>', methods=['GET','POST'])
@csrf.exempt
@login_required
def pagar_tarjeta(numero):
    pedido = Pedido.query.filter_by(numero_pedido=numero, usuario_id=current_user.id).first_or_404()
    if request.method == 'POST':
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(float(pedido.total) * 100),
                currency='pen',
                metadata={'pedido_id': pedido.id, 'numero': pedido.numero_pedido}
            )
            pedido.stripe_id = intent.id
            db.session.commit()
            return jsonify({'client_secret': intent.client_secret})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return render_template('checkout/pago_tarjeta.html', pedido=pedido,
                           STRIPE_PUBLIC_KEY=current_app.config['STRIPE_PUBLIC_KEY'])

@bp.route('/stripe/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    payload   = request.get_data()
    sig_header= request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, current_app.config['STRIPE_WEBHOOK_SECRET'])
    except Exception:
        return '', 400
    if event['type'] == 'payment_intent.succeeded':
        pi = event['data']['object']
        pedido = Pedido.query.filter_by(stripe_id=pi['id']).first()
        if pedido:
            pedido.estado_pago = 'pagado'
            pedido.estado      = 'confirmado'
            db.session.commit()
    return '', 200

@bp.route('/confirmacion/<numero>')
@login_required
def confirmacion(numero):
    pedido = Pedido.query.filter_by(numero_pedido=numero, usuario_id=current_user.id).first_or_404()
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
    pedido = Pedido.query.filter_by(numero_pedido=numero, usuario_id=current_user.id).first_or_404()
    return render_template('perfil/detalle_pedido.html', pedido=pedido)
