from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.pagedown import PageDown
from flask.ext.limiter import Limiter
from flask.ext.misaka import Misaka
from flask.ext.babel import Babel
from flask.ext.cache import Cache

from app.ext.flask_s3 import FlaskS3

from app.config import config, Config

from celery import Celery

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

limiter = Limiter()
md = Misaka()
babel = Babel()
s3 = FlaskS3()
cache = Cache()
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = "Xin vui lòng đăng nhập để truy cập trang"

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    limiter.init_app(app)
    md.init_app(app)
    babel.init_app(app)
    s3.init_app(app)
    cache.init_app(app)

    celery.conf.update(app.config)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        sslify = SSLify(app)

    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.settings import settings as settings_blueprint
    limiter.exempt(settings_blueprint)
    app.register_blueprint(settings_blueprint, url_prefix='/settings')

    from app.admin import admin as admin_blueprint
    limiter.exempt(admin_blueprint)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app
