import os
basedir = os.path.abspath(os.path.dirname(__file__))

PROJECT_NAME = 'VIETNOM'
def _get_key(KEY_NAME):
    """It's recommened to keep SECRET_KEY in environment variables, but don't
    keep it in plain text!!!
    """
    try:
        import keyring
        import random
        key = keyring.get_password(PROJECT_NAME, KEY_NAME)
        if key:
            return key
        elif KEY_NAME == 'SECRET_KEY':
            chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
            key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
            keyring.set_password(PROJECT_NAME, 'SECRET_KEY', key)
        return key
    except:
        pass

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or _get_key('SECRET_KEY')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or _get_key('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or _get_key('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[Việt Nôm]'
    MAIL_SENDER = 'Việt Nôm'
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN') or _get_key('MAIL_ADMIN')
    NOMS_PER_PAGE = 99
    POST_PER_PAGE = 7
    RATELIMIT_GLOBAL = '1/second'
    SSL_DISABLE = True

    S3_BUCKET_NAME = 'vietnom'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID') or \
        _get_key('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or \
        _get_key('AWS_SECRET_ACCESS_KEY')

    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 60
    CACHE_REDIS_URL = os.environ.get('REDISCLOUD_URL') or \
        'redis://localhost:6379'

    CELERY_BROKER_URL = os.environ.get('RABBITMQ_BIGWIG_URL') or \
        'amqp://localhost'
    CELERY_RESULT_BACKEND = os.environ.get('RABBITMQ_BIGWIG_URL') or \
        'amqp://localhost'
    CELERY_IMPORTS = ('app.email', )
    BABEL_DEFAULT_LOCALE = 'vi'


    @staticmethod
    def init_app(app):
        pass

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_ADMIN],
            subject=cls.MAIL_SUBJECT_PREFIX + ' Lỗi ứng dụng',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class TestingConfig(Config):
    TESTING = True
    # When using Travis-CI don't turn on `DEBUG`, but when testing locally
    # we should, shouldn't we?
    DEBUG = os.environ.get('DEBUG')
    SQLALCHEMY_DATABASE_URI = _get_key('TEST_DATABASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True
    # Don't use the same database with TESTING, it will drop all your tables
    SQLALCHEMY_DATABASE_URI = _get_key('DEV_DATABASE_URL')
    # USE_S3 = False

class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))
    S3_USE_HTTPS = False if SSL_DISABLE else True

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,

    'default': ProductionConfig,
}
