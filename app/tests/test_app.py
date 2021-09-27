import unittest
import re
from unittest import TestCase
from flask_login import login_user, logout_user, current_user, login_required

from app import create_app, db
from app.config import Config
from app.models import User, Team
from app.main.routes import NONE_OPTION


# Do not mess with the production db!
# Set config database to a test one!
Config.POSTGRES = {'db': 'warehouse_game_test',
                   'host': 'localhost',
                   'port': '5432',
                   'pw': '123',
                   'user': 'game'}
Config.REDIS_URL = 'redis://'
Config.SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % Config.POSTGRES


class BaseTest(TestCase):
    def setUp(self):
        self.app = create_app(Config)
        self.client = self.app.test_client()
        self._ctx = self.app.test_request_context()
        self._ctx.push()
        db.create_all()

    def create_app(self):
        print('create_app')
        return self.app

    def tearDown(self):
        with self._ctx:
            self._ctx.pop()
            db.session.remove()
            db.drop_all()

    def get_csrf(self, resp):
        csrf = re.search('name=\"csrf_token\".*value=\"(.*?)\">\\n', resp.data.decode('utf-8')).group(1)
        return csrf

    def add_admin_user(self, username, password):
        user = User(username=username)
        user.set_password(password)
        user.is_admin = True
        db.session.add(user)
        db.session.commit()
        return user

    def login_req(self, username, password):
        """ Make sure to use within a test context """
        login_resp = self.client.get('/auth/login')
        csrf = self.get_csrf(login_resp)
        resp = self.client.post('/auth/login', data=dict(
            username=username,
            password=password,
            csrf_token=csrf
        ), follow_redirects=True)
        return resp

    def login_admin(self):
        username = 'admin'
        password = '123'
        admin_user = self.add_admin_user(username, password)
        self.login_req(admin_user.username, password)
        return admin_user


class UserTest(BaseTest):
    """"""

    def test_user_authentication(self):
        with self.client:
            # (the test case should be within a test request context)
            username = 'TestUser1'
            password = '123'

            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            resp = self.login_req(username, password)
            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(current_user, user)

    def test_admin_authentication(self):
        with self.client:
            # (the test case should be within a test request context)
            username = 'TestAdminUser1'
            password = '123'

            user = User(username=username)
            user.set_password(password)
            user.is_admin = True
            db.session.add(user)
            db.session.commit()

            resp = self.login_req(username, password)

            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(current_user, user)
            self.assertIn(b'<a href="/auth/register">Register New User</a>', resp.data)
            self.assertIn(b'<li><a href="/games">Games</a>', resp.data)


class MainRoutesTest(BaseTest):

    def test_teams(self):
        with self.client:
            self.login_admin()

            resp = self.client.get('/teams')
            csrf_resp = self.get_csrf(resp)

            display_name = 'team1'
            resp = self.client.post('/teams', data=dict(
                csrf_token=csrf_resp,
                display_name=display_name,
                submit='Add'
            ), follow_redirects=True)

            team = Team.query.first()

            self.assertEqual(resp.status, '200 OK')
            self.assertTrue(team)
            self.assertEqual(team.display_name, display_name)

    def test_team_slash_id(self):
        with self.client:
            self.login_admin()

            display_name = 'team1'
            team = Team(display_name=display_name)
            db.session.add(team)
            db.session.commit()

            user = User(username='test_user')
            db.session.add(user)
            db.session.commit()

            resp = self.client.get(f'/teams/{team.id}')
            csrf_resp = self.get_csrf(resp)

            resp = self.client.post(f'/teams/{team.id}', data=dict(
                csrf_token=csrf_resp,
                add_user=user.id,
                remove_user=NONE_OPTION[0][0],
                submit='Save'
            ), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertTrue(team.users.all())

            resp = self.client.post(f'/teams/{team.id}', data=dict(
                csrf_token=csrf_resp,
                add_user=NONE_OPTION[0][0],
                remove_user=user.id,
                submit='Save'
            ), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertFalse(team.users.all())

    def test_user_slash_id(self):
        with self.client:
            self.login_admin()

            display_name = 'team1'
            team = Team(display_name=display_name)
            db.session.add(team)
            db.session.commit()

            user = User(username='test_user')
            db.session.add(user)
            db.session.commit()

            resp = self.client.get(f'/users/{user.id}')
            csrf_resp = self.get_csrf(resp)

            resp = self.client.post(f'/users/{user.id}', data=dict(
                csrf_token=csrf_resp,
                username='test_user2',
                display_name='test_user2',
                faculty_number='123',
                team_id=team.id,
                submit='Save'), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(user.username, 'test_user2')
            self.assertEqual(user.faculty_number, '123')
            self.assertEqual(user.team_id, team.id)


if __name__ == '__main__':
    unittest.main()
