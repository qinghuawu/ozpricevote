from flask import Flask
from flask_login import LoginManager
from config import Config
from model import User
from blueprints.home import home_bp
from blueprints.auth import auth_bp
from blueprints.user import user_bp
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)


def register_blueprints(the_app):
    the_app.register_blueprint(home_bp)
    the_app.register_blueprint(auth_bp)
    the_app.register_blueprint(user_bp)


app.config.from_object(Config())
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
CSRFProtect(app)
register_blueprints(app)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id).retrieve_user_by_id()
