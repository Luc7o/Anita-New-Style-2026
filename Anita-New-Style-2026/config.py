import os
from dotenv import load_dotenv
load_dotenv()

# Directorio raíz del proyecto (donde está config.py)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')

    DB_HOST     = os.environ.get('DB_HOST', 'mysql-USUARIO.alwaysdata.net')
    DB_PORT     = os.environ.get('DB_PORT', '3306')
    DB_USER     = os.environ.get('DB_USER', 'usuario_anita')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME     = os.environ.get('DB_NAME', 'usuario_anita_db')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"mysql+pymysql://{os.environ.get('DB_USER','u')}:{os.environ.get('DB_PASSWORD','')}@{os.environ.get('DB_HOST','localhost')}:{os.environ.get('DB_PORT','3306')}/{os.environ.get('DB_NAME','anita_db')}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    UPLOAD_FOLDER      = os.path.join(BASE_DIR, 'static', 'img', 'productos')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    STRIPE_PUBLIC_KEY     = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY     = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    YAPE_NUMERO = os.environ.get('YAPE_NUMERO', '999999999')
    YAPE_NOMBRE = os.environ.get('YAPE_NOMBRE', 'Anita New Style')

    MAIL_DESTINATARIO   = os.environ.get('MAIL_DESTINATARIO', os.environ.get('MAIL_USERNAME', ''))

    MAIL_SERVER         = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = True
    MAIL_USE_SSL        = False
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Anita New Style <noreply@anitanewstyle.com>')

    PRODUCTOS_POR_PAGINA = 12
    COSTO_ENVIO          = 8.00
    ENVIO_GRATIS_DESDE   = 150.00

    # ─── API Perú (DNI / RUC) ───────────────────────────────────────────────────
    API_PERU_TOKEN = os.environ.get('API_PERU_TOKEN', '')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
