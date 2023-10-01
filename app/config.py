import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(".env", usecwd=True))


class Config:
    """
    Common configurations
    """
    FLASK_APP = 'game.py'
    # FLASK_ENV = 'development'
    # FLASK_DEBUG = 'TRUE'
    ADMINS = ['admin@warehouse-game.com']
    LANGUAGES = ['en', 'es']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SECRET_KEY = os.environ.get('FLASK_APP_SECRET_KEY') or 'super-secret-key-that-you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    POSTGRES = {
        'user': os.environ.get('FLASK_APP_DATABASE_USER') or 'game',
        'pw': os.environ.get('FLASK_APP_DATABASE_PASSWORD') or '123',
        'db': os.environ.get('FLASK_APP_DATABASE_DB') or 'warehouse_game',
        'host': os.environ.get('FLASK_APP_DATABASE_HOST') or 'localhost',
        'port': os.environ.get('FLASK_APP_DATABASE_PORT') or '5432',
    }
    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
