import sys, os
# Añadir directorio del proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from app import create_app
application = create_app(os.environ.get('FLASK_ENV', 'production'))
