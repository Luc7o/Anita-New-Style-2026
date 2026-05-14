from app import create_app
from app_extensions import db
from models import Usuario, Categoria

app = create_app()

@app.cli.command('init-db')
def init_db():
    """Crea las tablas e inserta datos iniciales."""
    with app.app_context():
        db.create_all()
        # Categorías por defecto
        from models.producto import Categoria
        cats = [
            ('Calzados',   'calzados',   'boot'),
            ('Vestidos',   'vestidos',   'dress'),
            ('Carteras',   'carteras',   'handbag'),
            ('Mochilas',   'mochilas',   'backpack'),
            ('Accesorios', 'accesorios', 'gem'),
        ]
        for nombre, slug, icono in cats:
            if not Categoria.query.filter_by(slug=slug).first():
                db.session.add(Categoria(nombre=nombre, slug=slug, icono=icono))

        # Admin por defecto
        import os
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@anitanewstyle.com')
        if not Usuario.query.filter_by(email=admin_email).first():
            admin = Usuario(
                nombre='Administrador', apellido='Sistema',
                email=admin_email, es_admin=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'Admin123!'))
            db.session.add(admin)

        db.session.commit()
        print("✅ Base de datos inicializada correctamente.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
