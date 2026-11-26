import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Has d\'iniciar sessió per accedir a aquesta pàgina.'
login_manager.login_message_category = 'warning'


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Log version on startup
    from app.version import VERSION
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('web-pot')
    logger.info(f'=== Web-Pot v{VERSION} starting ===')

    # Ensure the data directory exists for SQLite
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('sqlite:////'):
        db_file = db_uri.replace('sqlite:////', '/')
        db_dir = os.path.dirname(db_file)
        os.makedirs(db_dir, exist_ok=True)
    elif db_uri.startswith('sqlite:///'):
        db_file = db_uri.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    logger.info(f'=== Web-Pot v{VERSION} ready ===')
    return app
