from flask import Blueprint, render_template, request, abort
from models.producto import Producto, Categoria
from app_extensions import db

bp = Blueprint('tienda', __name__)

@bp.route('/')
def inicio():
    destacados = Producto.query.filter_by(activo=True, destacado=True).limit(8).all()
    nuevos     = Producto.query.filter_by(activo=True, es_nuevo=True).order_by(Producto.fecha_creacion.desc()).limit(8).all()
    categorias = Categoria.query.filter_by(activo=True).all()
    return render_template('tienda/inicio.html', destacados=destacados, nuevos=nuevos, categorias=categorias)

@bp.route('/productos')
def productos():
    pagina     = request.args.get('pagina', 1, type=int)
    categoria  = request.args.get('categoria')
    orden      = request.args.get('orden', 'nuevo')
    busqueda   = request.args.get('q', '')
    precio_min = request.args.get('precio_min', type=float)
    precio_max = request.args.get('precio_max', type=float)

    query = Producto.query.filter_by(activo=True)

    if categoria:
        cat_obj = Categoria.query.filter_by(slug=categoria).first_or_404()
        query = query.filter_by(categoria_id=cat_obj.id)
    else:
        cat_obj = None

    if busqueda:
        query = query.filter(Producto.nombre.ilike(f'%{busqueda}%'))
    if precio_min:
        query = query.filter(Producto.precio >= precio_min)
    if precio_max:
        query = query.filter(Producto.precio <= precio_max)

    if orden == 'precio_asc':
        query = query.order_by(Producto.precio.asc())
    elif orden == 'precio_desc':
        query = query.order_by(Producto.precio.desc())
    elif orden == 'popular':
        query = query.order_by(Producto.vendidos.desc())
    else:
        query = query.order_by(Producto.fecha_creacion.desc())

    paginacion = query.paginate(page=pagina, per_page=12, error_out=False)
    return render_template('tienda/productos.html',
        productos=paginacion, categoria_sel=cat_obj,
        orden=orden, busqueda=busqueda,
        precio_min=precio_min, precio_max=precio_max)

@bp.route('/producto/<int:id>')
def detalle_producto(id):
    producto   = Producto.query.filter_by(id=id, activo=True).first_or_404()
    producto.vistas += 1
    db.session.commit()
    relacionados = Producto.query.filter(
        Producto.categoria_id == producto.categoria_id,
        Producto.id != producto.id,
        Producto.activo == True
    ).limit(4).all()
    return render_template('tienda/producto_detalle.html', producto=producto, relacionados=relacionados)
