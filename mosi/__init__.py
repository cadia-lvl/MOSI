"""Initialize Flask app."""
import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_security import (Security, SQLAlchemyUserDatastore)
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix
from flask_executor import Executor


from mosi.forms import ExtendedLoginForm
from mosi.models import User, Role
from mosi.models import db as sqlalchemy_db
from mosi.filters import format_date

from mosi.views.main import main
from mosi.views.token import token
from mosi.views.recording import recording
from mosi.views.user import user
#from mosi.views.configuration import configuration
from mosi.views.mos import mos
from mosi.views.abtest import abtest




def create_app():
    user_datastore = SQLAlchemyUserDatastore(sqlalchemy_db, User, Role)
    app = Flask(__name__)

    if os.getenv('SEMI_PROD', False):
        app.config.from_pyfile('{}.py'.format(os.path.join(
            'settings', 'semi_production')))
    else:
        app.config.from_pyfile('{}.py'.format(os.path.join(
            'settings', os.getenv('FLASK_ENV', 'development'))))
    if 'REVERSE_PROXY_PATH' in app.config:
        ReverseProxyPrefixFix(app)

    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(create_logger(app.config['LOG_PATH']))

    sqlalchemy_db.init_app(app)
    Security(app, user_datastore, login_form=ExtendedLoginForm)

    # register filters
    app.jinja_env.filters['datetime'] = format_date

    # Propagate background task exceptions
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
    # register blueprints
    app.register_blueprint(main)
    app.register_blueprint(user)
    #app.register_blueprint(configuration)
    app.register_blueprint(mos)
    app.register_blueprint(abtest)

    app.executor = Executor(app)
    app.user_datastore = user_datastore

    return app


def create_logger(log_path: str):
    logfile_mode = 'w'
    if os.path.exists(log_path):
        logfile_mode = 'a'
    else:
        os.makedirs(os.path.split(log_path)[0])
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1000,
        backupCount=1,
        mode=logfile_mode)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    return handler


app = create_app()
