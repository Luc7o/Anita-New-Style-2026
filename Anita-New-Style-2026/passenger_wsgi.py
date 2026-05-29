import sys, os

# Directorio absoluto del proyecto
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Agregar al path de Python
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Directorio de trabajo
os.chdir(PROJECT_DIR)

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

from app import create_app
application = create_app(os.environ.get('FLASK_ENV', 'production'))