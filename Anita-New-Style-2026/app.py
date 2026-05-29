import os
from flask import Flask, render_template, send_from_directory
from config import config, BASE_DIR
from app_extensions import db, login, mail, migrate, csrf


def create_app(env=None):
    app = Flask(__name__)

    # Configuración del entorno
    env = env or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config.get(env, config['default']))

    # Ruta absoluta garantizada para uploads (independiente del CWD del servidor)
    upload_folder = os.path.join(BASE_DIR, 'static', 'img', 'productos')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # Ruta dedicada para servir imágenes de productos
    # Soluciona el problema de visibilidad en hosting compartido (AlwaysData/Passenger)
    @app.route('/static/img/productos/<path:filename>')
    def imagen_producto(filename):
        return send_from_directory(upload_folder, filename)

    # Extensiones
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # User loader
    from models.usuario import Usuario

    @login.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Blueprints
    from routes.auth import bp as auth_bp
    from routes.tienda import bp as tienda_bp
    from routes.carrito import bp as carrito_bp
    from routes.pedidos import bp as pedidos_bp
    from routes.perfil import bp as perfil_bp
    from routes.admin import bp as admin_bp
    from routes.api import bp as api_bp

    csrf.exempt(api_bp)

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(tienda_bp)
    app.register_blueprint(carrito_bp, url_prefix='/carrito')
    app.register_blueprint(pedidos_bp, url_prefix='/pedidos')
    app.register_blueprint(perfil_bp, url_prefix='/perfil')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Context processor
    @app.context_processor
    def inyectar_globales():
        from models.producto import Categoria
        from models.carrito import ItemCarrito
        from flask_login import current_user

        categorias = Categoria.query.filter_by(activo=True).all()

        cant_carrito = 0
        if current_user.is_authenticated:
            cant_carrito = ItemCarrito.query.filter_by(usuario_id=current_user.id).count()

        return dict(
            categorias=categorias,
            cant_carrito=cant_carrito,
            YAPE_NUMERO=app.config['YAPE_NUMERO'],
            STRIPE_PUBLIC_KEY=app.config['STRIPE_PUBLIC_KEY']
        )

    # Filtros Jinja
    @app.template_filter('moneda')
    def filtro_moneda(valor):
        return f"S/ {float(valor or 0):.2f}"

    @app.template_filter('fecha_hora')
    def filtro_fecha_hora(dt):
        return dt.strftime('%d/%m/%Y %H:%M') if dt else '—'

    @app.template_filter('fecha_corta')
    def filtro_fecha_corta(dt):
        return dt.strftime('%d/%m/%Y') if dt else '—'

    # Errores
    @app.errorhandler(404)
    def pagina_no_encontrada(e):
        return render_template('errores/404.html'), 404

    @app.errorhandler(500)
    def error_servidor(e):
        return render_template('errores/500.html'), 500

    return app


# Arranque directo
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
