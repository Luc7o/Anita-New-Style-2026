from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db       = SQLAlchemy()
login    = LoginManager()
mail     = Mail()
migrate  = Migrate()
csrf     = CSRFProtect()

login.login_view              = 'auth.login'
login.login_message           = 'Por favor inicia sesión para continuar.'
login.login_message_category  = 'warning'
