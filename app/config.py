import os


class Config:
    """
    Common configurations
    """
    # FLASK_APP = 'game.py'
    # FLASK_ENV = 'development'
    # FLASK_DEBUG = 'TRUE'

    SECRET_KEY = os.environ.get('FLASK_APP_SECRET_KEY') or 'super-secret-key-that-you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTGRES = {
        'user': os.environ.get('FLASK_APP_DATABASE_USER') or 'game',
        'pw': os.environ.get('FLASK_APP_DATABASE_PASSWORD') or '123',
        'db': os.environ.get('FLASK_APP_DATABASE_DB') or 'warehouse_game',
        'host': os.environ.get('FLASK_APP_DATABASE_HOST') or 'localhost',
        'port': os.environ.get('FLASK_APP_DATABASE_PORT') or '5432',
    }

    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
