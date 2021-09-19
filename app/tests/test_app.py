# import os
# import tempfile
#
# import pytest
#
# from app import db, create_app
# from app.config import Config
#
#
# @pytest.fixture
# def client():
#     Config.TESTING = True
#     Config.POSTGRES.update({
#         'user': 'game',
#         'pw': '123',
#         'db': 'warehouse_game_test'
#     })
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
#     resp = client.get('/')
#     assert b'<title>\n    Warehouse\n</title>\n' in resp.data
#
#
import os

import unittest
from flask_testing import TestCase
from flask_sqlalchemy import SQLAlchemy


from app import create_app
from app.config import Config
from app.models import User


class MyTest(TestCase):

    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    REDIS_URL = Config.REDIS_URL
    LANGUAGES = Config.LANGUAGES

    def create_app(self):
        # pass in test configuration
        return create_app(Config)

    def setUp(self):
        self.db = SQLAlchemy(self.app)
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()


class SomeTest(MyTest):

    def login(self, username, password):
        return self.client.post('/auth/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_login_stuff(self):
        username = 'joro3'
        password = '123'

        resp = self.login(username, password)
        assert b'You were logged in' in resp.data

    def test_something(self):

        user = User()
        self.db.session.add(user)
        self.db.session.commit()

        # this works
        assert user in self.db.session

        response = self.client.get("/")

        # this raises an AssertionError
        assert user in self.db.session


if __name__ == '__main__':
    unittest.main()
