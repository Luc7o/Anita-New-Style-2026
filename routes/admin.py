import os, uuid, json
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app_extensions import db
from models.producto import Producto, Categoria, ImagenProducto
from models.pedido   import Pedido, DetallePedido
from models.usuario  import Usuario
from forms.producto_forms import FormProducto, FormCategoria

bp = Blueprint('admin', __name__)

def admin_requerido(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.es_admin:
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('tienda.inicio'))
        return f(*args, **kwargs)
    return decorated

def _guardar_imagen(archivo):
    ext    = archivo.filename.rsplit('.', 1)[-1].lower()
    nombre = f"prod_{uuid.uuid4().hex[:12]}.{ext}"
    ruta   = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre)
    archivo.save(ruta)
    return nombre

# ── Dashboard ──────────────────────────────────────────────────────────────────
@bp.route('/')
@admin_requerido
def dashboard():
    from sqlalchemy import func
    total_ventas   = db.session.query(func.sum(Pedido.total)).filter(Pedido.estado_pago=='pagado').scalar() or 0
    total_pedidos  = Pedido.query.count()
    total_clientes = Usuario.query.filter_by(es_admin=False).count()
    total_productos= Producto.query.filter_by(activo=True).count()
    ultimos_pedidos= Pedido.query.order_by(Pedido.fecha_creacion.desc()).limit(10).all()
    sin_stock      = Producto.query.filter(Producto.stock <= 0, Producto.activo==True).count()
    # Ventas por categoría
    ventas_cat = db.session.query(
        Categoria.nombre,
        func.sum(DetallePedido.subtotal).label('total')
    ).join(Producto, Producto.id==DetallePedido.producto_id)\
     .join(Categoria, Categoria.id==Producto.categoria_id)\
     .join(Pedido, Pedido.id==DetallePedido.pedido_id)\
     .filter(Pedido.estado_pago=='pagado')\
     .group_by(Categoria.nombre).all()

    return render_template('admin/dashboard.html',
        total_ventas=total_ventas, total_pedidos=total_pedidos,
        total_clientes=total_clientes, total_productos=total_productos,
        ultimos_pedidos=ultimos_pedidos, sin_stock=sin_stock,
        ventas_cat=ventas_cat)

# ── Productos ──────────────────────────────────────────────────────────────────
@bp.route('/productos')
@admin_requerido
def productos():
    pagina   = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('q', '')
    query    = Producto.query
    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))
    prods = query.order_by(Producto.fecha_creacion.desc()).paginate(page=pagina, per_page=20)
    return render_template('admin/productos.html', productos=prods, busqueda=busqueda)

@bp.route('/productos/nuevo', methods=['GET','POST'])
@admin_requerido
def nuevo_producto():
    form = FormProducto()
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
    if form.validate_on_submit():
        tallas = json.dumps([t.strip() for t in form.tallas.data.split(',') if t.strip()]) if form.tallas.data else None
        colores= json.dumps([c.strip() for c in form.colores.data.split(',') if c.strip()]) if form.colores.data else None
        prod   = Producto(
            nombre=form.nombre.data, descripcion=form.descripcion.data,
            precio=form.precio.data, precio_oferta=form.precio_oferta.data or None,
            categoria_id=form.categoria_id.data, tallas=tallas, colores=colores,
            stock=form.stock.data, sku=form.sku.data or None,
            destacado=form.destacado.data, es_nuevo=form.es_nuevo.data, activo=form.activo.data,
        )
        if form.imagen.data and form.imagen.data.filename:
            prod.imagen_principal = _guardar_imagen(form.imagen.data)
        db.session.add(prod)
        db.session.commit()
        flash('Producto creado exitosamente.', 'success')
        return redirect(url_for('admin.productos'))
    return render_template('admin/producto_form.html', form=form, titulo='Nuevo producto')

@bp.route('/productos/<int:id>/editar', methods=['GET','POST'])
@admin_requerido
def editar_producto(id):
    prod = Producto.query.get_or_404(id)
    form = FormProducto(obj=prod)
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.filter_by(activo=True).all()]
    if request.method == 'GET':
        form.tallas.data = ', '.join(prod.tallas_lista)
        form.colores.data= ', '.join(prod.colores_lista)
    if form.validate_on_submit():
        prod.nombre        = form.nombre.data
        prod.descripcion   = form.descripcion.data
        prod.precio        = form.precio.data
        prod.precio_oferta = form.precio_oferta.data or None
        prod.categoria_id  = form.categoria_id.data
        prod.tallas        = json.dumps([t.strip() for t in form.tallas.data.split(',') if t.strip()]) if form.tallas.data else None
        prod.colores       = json.dumps([c.strip() for c in form.colores.data.split(',') if c.strip()]) if form.colores.data else None
        prod.stock         = form.stock.data
        prod.sku           = form.sku.data or None
        prod.destacado     = form.destacado.data
        prod.es_nuevo      = form.es_nuevo.data
        prod.activo        = form.activo.data
        if form.imagen.data and form.imagen.data.filename:
            prod.imagen_principal = _guardar_imagen(form.imagen.data)
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('admin.productos'))
    return render_template('admin/producto_form.html', form=form, titulo='Editar producto', producto=prod)

@bp.route('/productos/<int:id>/eliminar', methods=['POST'])
@admin_requerido
def eliminar_producto(id):
    prod = Producto.query.get_or_404(id)
    prod.activo = False
    db.session.commit()
    flash('Producto desactivado.', 'warning')
    return redirect(url_for('admin.productos'))

# ── Pedidos ────────────────────────────────────────────────────────────────────
@bp.route('/pedidos')
@admin_requerido
def pedidos():
    pagina = request.args.get('pagina', 1, type=int)
    estado = request.args.get('estado', '')
    query  = Pedido.query
    if estado:
        query = query.filter_by(estado=estado)
    peds = query.order_by(Pedido.fecha_creacion.desc()).paginate(page=pagina, per_page=20)
    return render_template('admin/pedidos.html', pedidos=peds, estado_sel=estado, ESTADOS=Pedido.ESTADOS)

@bp.route('/pedidos/<int:id>')
@admin_requerido
def ver_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    return render_template('admin/pedido_detalle.html', pedido=pedido)

@bp.route('/pedidos/<int:id>/estado', methods=['POST'])
@admin_requerido
def cambiar_estado(id):
    pedido = Pedido.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    if nuevo_estado in Pedido.ESTADOS:
        pedido.estado = nuevo_estado
        if nuevo_estado in ('entregado', 'confirmado') and pedido.metodo_pago in ('efectivo','recojo'):
            pedido.estado_pago = 'pagado'
        db.session.commit()
        flash(f'Estado actualizado a: {pedido.estado_label}', 'success')
    return redirect(url_for('admin.ver_pedido', id=id))

# ── Clientes ───────────────────────────────────────────────────────────────────
@bp.route('/clientes')
@admin_requerido
def clientes():
    pagina   = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('q', '')
    query    = Usuario.query.filter_by(es_admin=False)
    if busqueda:
        query = query.filter(
            (Usuario.nombre.ilike(f'%{busqueda}%')) |
            (Usuario.email.ilike(f'%{busqueda}%'))
        )
    clientes = query.order_by(Usuario.fecha_registro.desc()).paginate(page=pagina, per_page=20)
    return render_template('admin/clientes.html', clientes=clientes, busqueda=busqueda)

@bp.route('/clientes/<int:id>')
@admin_requerido
def ver_cliente(id):
    cliente = Usuario.query.get_or_404(id)
    pedidos = Pedido.query.filter_by(usuario_id=id).order_by(Pedido.fecha_creacion.desc()).all()
    return render_template('admin/cliente_detalle.html', cliente=cliente, pedidos=pedidos)

@bp.route('/clientes/<int:id>/toggle', methods=['POST'])
@admin_requerido
def toggle_cliente(id):
    cliente = Usuario.query.get_or_404(id)
    cliente.activo = not cliente.activo
    db.session.commit()
    estado = 'activado' if cliente.activo else 'desactivado'
    flash(f'Cliente {estado}.', 'info')
    return redirect(url_for('admin.clientes'))

# ── Categorías ─────────────────────────────────────────────────────────────────
@bp.route('/categorias')
@admin_requerido
def categorias():
    cats = Categoria.query.all()
    return render_template('admin/categorias.html', categorias=cats)

@bp.route('/categorias/nueva', methods=['GET','POST'])
@admin_requerido
def nueva_categoria():
    form = FormCategoria()
    if form.validate_on_submit():
        
        slug = form.slug.data or form.nombre.data.lower().replace(" ", "-").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        cat  = Categoria(nombre=form.nombre.data, slug=slug,
                         descripcion=form.descripcion.data,
                         icono=form.icono.data, activo=form.activo.data)
        db.session.add(cat)
        db.session.commit()
        flash('Categoría creada.', 'success')
        return redirect(url_for('admin.categorias'))
    return render_template('admin/categoria_form.html', form=form, titulo='Nueva categoría')
