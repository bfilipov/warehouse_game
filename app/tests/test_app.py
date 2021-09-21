# import os
# import tempfile
#
# import pytest
# from flask_sqlalchemy import SQLAlchemy
#
# from app import create_app
# from app.config import Config
# from flask_migrate import upgrade, Migrate
#
# db = SQLAlchemy()
#
# @pytest.fixture
# def client():
#     Config.TESTING = True
#     Config.POSTGRES.update({
#         'user': 'game',
#         'pw': '123',
#         'db': 'warehouse_game_test'
#     })
#     Config.SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % Config.POSTGRES
#     app = create_app(Config)
#     with app.test_client() as client:
#         yield client
#
#
# def login(client, username, password):
#     return client.post('/auth/login', data=dict(
#         username=username,
#         password=password
#     ), follow_redirects=True)
#
#
# def logout(client):
#     return client.get('/logout', follow_redirects=True)
#
#
# def test_empty_db(client):
#     """Start with a blank database."""
#     import pdb; pdb.set_trace()
#     resp = client.get('/')
#     assert b'<title>\n    Warehouse\n</title>\n' in resp.data
#
#


### -------------------------------------------------------



# import os
#
# import unittest
# from flask_migrate import upgrade, Migrate
# from flask_testing import TestCase
# from flask_sqlalchemy import SQLAlchemy
#
#
# from app import create_app
# from app.config import Config
# from app.models import User
#
# # Change config database to a test one!
# Config.POSTGRES = {'db': 'warehouse_game_test',
#                    'host': 'localhost',
#                    'port': '5432',
#                    'pw': '123',
#                    'user': 'game'}
# Config.REDIS_URL = 'redis://'
# Config.SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % Config.POSTGRES
#
# app = create_app(Config)
# db = SQLAlchemy(app)
# from app import models
#
#
# class MyTest(TestCase):
#
#     @classmethod
#     def setUpClass(cls):
#         # run alembic migrations on test db
#         with app.app_context():
#             db.create_all()
#             migrate = Migrate()
#             migrate.init_app(app, db)
#             import pdb;
#             pdb.set_trace()
#             upgrade()
#
#
#     def create_app(self):
#         # print('create app')
#         # db.create_all()
#         # return create_app(Config)
#         return app
#
#     def setUp(self):
#         print('setup ')
#
#     def tearDown(self):
#         pass
#         # db.session.remove()
#         # db.drop_all()
#
#     @classmethod
#     def tearDownClass(cls):
#         pass
#         # db.engine.execute("DROP TABLE alembic_version")
#         # print("tearDownClass")
#
#
# class LoginTest(MyTest):
#
#     def login(self, username, password):
#         return self.client.post('/auth/login', data=dict(
#             username=username,
#             password=password
#         ), follow_redirects=True)
#
#     def test_create_user_and_login(self):
#         # create an admin user first
#         admin = User(is_admin=True,
#                      username='admin',
#                      email='admin@abv.bg')
#         admin.set_password('admin_pass_you_will_never_guess')
#         db.session.add(admin)
#         db.session.commit()
#
#         username = 'joro3'
#         password = '123'
#
#         self.client.post('/auth/register', data=dict(
#             username=username,
#             password=password
#         ), follow_redirects=True)
#
#         resp = self.login(username, password)
#         assert b'You were logged in' in resp.data
#
#     def test_something(self):
#         pass
#
#         # user = User()
#         # self.db.session.add(user)
#         # self.db.session.commit()
#
#         # this works
#         # assert user in self.db.session
#         #
#         # response = self.client.get("/")
#         #
#         # # this raises an AssertionError
#         # assert user in self.db.session
#
#
# if __name__ == '__main__':
#     unittest.main()



###############-------------------------------------------------------------------------

import unittest
from unittest import TestCase

from app import create_app, db
from app.config import Config
from app.models import User
from flask_login import login_user, logout_user, current_user, login_required
# from flask_security.utils import login_user

# Change config database to a test one!
Config.POSTGRES = {'db': 'warehouse_game_test',
                   'host': 'localhost',
                   'port': '5432',
                   'pw': '123',
                   'user': 'game'}
Config.REDIS_URL = 'redis://'
Config.SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % Config.POSTGRES


class UserTest(TestCase):

    def create_app(self):
        print('create_app')
        return self.app

    def setUp(self):
        print('setup ')
        self.app = create_app(Config)
        self.client = self.app.test_client()
        self._ctx = self.app.test_request_context()
        self._ctx.push()
        db.create_all()

    def tearDown(self):
        with self._ctx:
            self._ctx.pop()
            db.session.remove()
            db.drop_all()

    def test_user_authentication(self):
        with self._ctx:
            print('here!')
            # (the test case is within a test request context)
            user = User(username='TestUSer1')
            user.set_password('123')
            db.session.add(user)
            db.session.commit()
            login_user(user)

        # current_user here is the user
        print(current_user)

        # current_user within this request is an anonymous user
        r = self.client.get('/user')


if __name__ == '__main__':
    unittest.main()
