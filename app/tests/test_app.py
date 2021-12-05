import re
import unittest
from functools import wraps
from unittest import TestCase

from flask_login import login_user, logout_user, current_user, login_required

import app.main.routes as routes
from app import create_app, db
from app.config import Config
from app.models import Activity, Game, Input, Penalty, Team, TeamActivity, User



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
        return self.app

    def tearDown(self):
        with self._ctx:
            self._ctx.pop()
            db.session.remove()
            db.drop_all()

    def get_csrf(self, resp):
        csrf = re.search('name=\"csrf_token\".*value=\"(.*?)\">\\n', resp.data.decode('utf-8')).group(1)
        return csrf

    def add_user(self, username, password, is_admin=False):
        _user = User(username=username, is_admin=is_admin)
        _user.set_password(password)
        db.session.add(_user)
        db.session.commit()
        return _user

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

    def login_user(self):
        username = 'user1'
        password = '123'
        user = self.add_user(username, password)
        self.login_req(user.username, password)
        return user

    def login_admin(self):
        username = 'admin'
        password = '123'
        admin_user = self.add_user(username, password, is_admin=True)
        self.login_req(admin_user.username, password)
        return admin_user


class UserTest(BaseTest):
    """"""

    def test_user_authentication(self):
        with self.client:
            # (the test case should be within a test request context)
            username = 'TestUser1'
            password = '123'
            user = self.add_user(username, password)
            resp = self.login_req(username, password)
            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(current_user, user)

    def test_admin_authentication(self):
        with self.client:
            # (the test case should be within a test request context)
            username = 'TestAdminUser1'
            password = '123'
            user = self.add_user(username, password, is_admin=True)
            resp = self.login_req(username, password)

            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(current_user, user)
            self.assertIn(b'<a href="/auth/register">Register New User</a>', resp.data)
            self.assertIn(b'<li><a href="/games">Games</a>', resp.data)


class MainRoutesTest(BaseTest):

    def test_teams(self):
        """Test /teams endpoint
        Add new team"""
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
        """Test /teams/<id> endpoint
        Add new user to team"""
        with self.client:
            self.login_admin()
            team = routes.commit_object_to_db(Team, display_name='team1')
            user = routes.commit_object_to_db(User, username='test_user')

            resp = self.client.get(f'/teams/{team.id}')
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post(f'/teams/{team.id}', data=dict(
                csrf_token=csrf_resp,
                add_user=user.id,
                remove_user=routes.NONE_OPTION[0][0],
                submit='Save'
            ), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertTrue(team.users.all())

            resp = self.client.post(f'/teams/{team.id}', data=dict(
                csrf_token=csrf_resp,
                add_user=routes.NONE_OPTION[0][0],
                remove_user=user.id,
                submit='Save'
            ), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertFalse(team.users.all())

    def test_user_slash_id(self):
        """Test /users/<id> endpoint
        Update user data from admin panel"""
        with self.client:
            self.login_admin()
            team = routes.commit_object_to_db(Team, display_name='team1')
            user = routes.commit_object_to_db(User, username='test_user')

            resp = self.client.get(f'/users/{user.id}')
            csrf_resp = self.get_csrf(resp)

            resp = self.client.post(f'/users/{user.id}', data=dict(
                csrf_token=csrf_resp,
                username='test_user2',
                display_name='test_user2',
                team_id=team.id,
                submit='Save'), follow_redirects=True)

            self.assertEqual(resp.status, '200 OK')
            self.assertEqual(user.username, 'test_user2')
            self.assertEqual(user.team_id, team.id)

    def test_games(self):
        """Test /games endpoint
        """
        with self.client:
            user = self.login_admin()

            # assert regular admin cannot add games
            resp = self.client.get(f'/games')
            self.assertFalse('value="New Game"' in str(resp.data))

            # superadmin can add new games
            user.is_superadmin = True
            routes.commit_to_db(user)
            resp = self.client.get(f'/games')
            self.assertTrue('value="New Game"' in str(resp.data))

            # there are no games
            games = Game.query.all()
            self.assertTrue(len(games) == 0)

            # now add a new game
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post(f'/games', data=dict(
                csrf_token=csrf_resp,
                submit='New Game'), follow_redirects=True)

            # there is a game
            self.assertEqual(resp.status, '200 OK')
            games = Game.query.all()
            self.assertTrue(len(games) == 1)

    def test_edit_game(self):
        """Test /games/<id>/edit endpoint
        """
        with self.client:
            self.login_admin()
            game = routes.commit_object_to_db(Game)
            assigned_team = routes.commit_object_to_db(Team, display_name='team1', game_id=game.id)
            team2 = routes.commit_object_to_db(Team, display_name='team2')

            # options are polulated with coresponding teams
            resp = self.client.get(f'/games/{game.id}/edit')
            self.assertEqual(resp.status, '200 OK')
            self.assertTrue(
                '<select class="form-control" id="add_team" name="add_team" required>'
                '<option value="none_of_the_above">-</option><option value="2">Team 2,'
                ' team2</option></select>'
                in str(resp.data))
            self.assertTrue(
                '<select class="form-control" id="remove_team" name="remove_team" required>'
                '<option value="none_of_the_above">-</option><option value="1">Team 1, team1'
                '</option></select>'
                in str(resp.data))

            # assign unassigned team
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post(f'/games/{game.id}/edit', data=dict(
                csrf_token=csrf_resp,
                add_team=team2.id,
                remove_team='none_of_the_above',
                submit='Save'), follow_redirects=True)

            # unassigned team2 is now assigned
            self.assertTrue([i for i in game.teams] == [assigned_team, team2])
            self.assertEqual(resp.status, '200 OK')

            # make a new req since we've been redirected
            resp = self.client.get(f'/games/{game.id}/edit')
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post(f'/games/{game.id}/edit', data=dict(
                csrf_token=csrf_resp,
                add_team='none_of_the_above',
                remove_team=team2.id,
                submit='Save'), follow_redirects=True)

            # team2 is now unassigned again
            self.assertTrue([i for i in game.teams] == [assigned_team])
            self.assertEqual(resp.status, '200 OK')


class MainGameRoutesTest(BaseTest):

    def test_game_good_weather(self):
        """
        Test endpoint game/<id> increase decrease period functuionality
        """
        with self.client:
            self.login_admin()
            activity = routes.commit_object_to_db(Activity, id='A', days_needed=20, cost=1800)
            game = routes.commit_object_to_db(Game)
            team = routes.commit_object_to_db(Team, display_name='team1', game_id=game.id)
            input_ = routes.get_current_period_input(team, game)
            input_.credit_to_take = 300
            routes.commit_to_db(input_)
            team_act = routes.commit_object_to_db(TeamActivity,
                                                  id=f'{game.id}_{team.id}_A', input_id=input_.id)
            routes.set_team_activity(team_act, team, game)
            start_day = game.current_day

            # increase period through endpoint
            resp = self.client.get(f'/games/{game.id}')
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post(f'/games/{game.id}', data=dict(
                csrf_token=csrf_resp,
                increase_period='increase',
                submit='Save'
            ))
            inputs = Input.query.all()
            old_period, new_period = inputs
            ta = TeamActivity.query.first()
            penalties = Penalty.query.all()

            self.assertEqual(ta.initiated_on_day, start_day)
            self.assertEqual(ta.started_on_day, start_day)
            self.assertEqual(ta.first_time_ever_initiated_on_day, start_day)
            self.assertEqual(ta.finished_on_day, start_day + activity.days_needed)
            self.assertEqual(old_period.money_at_start_of_period, 2100)
            self.assertEqual(old_period.money_at_end_of_period,
                             new_period.money_at_start_of_period)
            self.assertEqual(
                new_period.money_at_start_of_period,
                (old_period.money_at_start_of_period
                 + old_period.credit_to_take
                 - activity.cost
                 - new_period.interest_cost
                 - new_period.total_penalty_cost)
            )
            self.assertEqual(new_period.active_at_day, start_day + routes.PERIOD_INCREMENT_IN_DAYS)
            self.assertTrue(len(penalties) == 0)

    def test_game_bad_weather(self):
        """Test endpoint game/<id> increase decrease period functuionality,
        start two activities, without available funds for the second one"""
        with self.client:
            self.login_admin()
            activity1 = routes.commit_object_to_db(Activity, id='A', days_needed=20, cost=1800)
            activity2 = routes.commit_object_to_db(Activity, id='B', days_needed=10, cost=600)
            game = routes.commit_object_to_db(Game)
            team = routes.commit_object_to_db(Team, display_name='team1', game_id=game.id)
            input_ = routes.get_current_period_input(team, game)
            input_.credit_to_take = 300
            routes.commit_to_db(input_)
            team_act1 = routes.commit_object_to_db(TeamActivity,
                                                   id=f'{game.id}_{team.id}_{activity1.id}',
                                                   input_id=input_.id)
            routes.set_team_activity(team_act1, team, game)
            team_act2 = routes.commit_object_to_db(TeamActivity,
                                                   id=f'{game.id}_{team.id}_{activity2.id}',
                                                   input_id=input_.id)
            routes.set_team_activity(team_act2, team, game)
            start_day = game.current_day

            # increase period through endpoint
            resp = self.client.get(f'/games/{game.id}')
            csrf_resp = self.get_csrf(resp)

            resp = self.client.post(f'/games/{game.id}', data=dict(
                csrf_token=csrf_resp,
                increase_period='increase',
                submit='Save'
            ))
            inputs = Input.query.all()
            old_period, new_period = inputs
            ta1 = TeamActivity.query.filter_by(activity_id='A').first()
            ta2 = TeamActivity.query.filter_by(activity_id='B').first()
            penalties = Penalty.query.all()

            # started one
            self.assertEqual(ta1.initiated_on_day, start_day)
            self.assertEqual(ta1.started_on_day, start_day)
            self.assertEqual(ta1.finished_on_day, start_day + activity1.days_needed)
            self.assertEqual(ta1.first_time_ever_initiated_on_day, start_day)

            # not started one
            self.assertEqual(ta2.started_on_day, routes.MAX_DAY)
            self.assertEqual(ta2.initiated_on_day, old_period.active_at_day)
            self.assertEqual(ta2.finished_on_day, routes.MAX_DAY)
            self.assertEqual(ta2.first_time_ever_initiated_on_day, start_day)

            self.assertEqual(old_period.money_at_start_of_period, 2100)
            self.assertEqual(old_period.money_at_end_of_period,
                             new_period.money_at_start_of_period)
            self.assertEqual(
                new_period.money_at_start_of_period,
                (old_period.money_at_start_of_period
                 + old_period.credit_to_take
                 - activity1.cost
                 - new_period.interest_cost
                 - new_period.total_penalty_cost)
            )
            self.assertEqual(new_period.active_at_day, start_day + routes.PERIOD_INCREMENT_IN_DAYS)
            self.assertTrue(len(penalties) == 1)

    def test_play_get(self):
        """Test endpoint /play
        get, post, increase_period"""
        with self.client:
            user = self.login_user()
            user.is_manager = True
            activity1 = routes.commit_object_to_db(Activity, title='A', id='A',
                                                   days_needed=20, cost=1800)
            activity2 = routes.commit_object_to_db(Activity, title='B', id='B',
                                                   days_needed=10, cost=600)
            game = routes.commit_object_to_db(Game)
            team = routes.commit_object_to_db(Team, display_name='team1', game_id=game.id)
            team.users.append(user)
            routes.commit_to_db(team)
            routes.commit_to_db(user)

            input_ = routes.get_current_period_input(team, game)
            routes.commit_to_db(input_)
            team_act1 = routes.commit_object_to_db(TeamActivity,
                                                   id=f'{game.id}_{team.id}_{activity1.id}',
                                                   input_id=input_.id)
            # routes.set_team_activity(team_act1, team, game)
            team_act2 = routes.commit_object_to_db(TeamActivity,
                                                   id=f'{game.id}_{team.id}_{activity2.id}',
                                                   input_id=input_.id)
            # routes.set_team_activity(team_act2, team, game)

            resp = self.client.get('/play', follow_redirects=True)

            self.assertTrue(r'<h3>Current day: 1</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Available funds: 2100.00</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Credit total: 2100</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Current round stats:</h3>' in str(resp.data))
            self.assertTrue(r'<h4>Penalties cost: 0</h4>' in str(resp.data))
            self.assertTrue(r'<h4>Rent cost: 0</h4>' in str(resp.data))
            self.assertTrue(r'<h4>Credit costs: 0.00</h4>' in str(resp.data))
            self.assertTrue(r'<h3>Activities finished:</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Activities in progress:</h3>' in str(resp.data))
            self.assertTrue(r'<h4>Credit costs: 0.00</h4>' in str(resp.data))

            csrf_resp = self.get_csrf(resp)
            resp = self.client.post('/play', data=dict(
                csrf_token=csrf_resp,
                add_activity=activity1.id,
                remove_activity=routes.NONE_OPTION[0][0],
                apply_for_credit=0,
                submit='Save'
            ), follow_redirects=True)

            csrf_resp = self.get_csrf(resp)
            resp = self.client.post('/play', data=dict(
                csrf_token=csrf_resp,
                add_activity=activity2.id,
                remove_activity=routes.NONE_OPTION[0][0],
                apply_for_credit=300,
                submit='Save'
            ), follow_redirects=True)

            self.assertTrue(r'<h3>Credit to be taken for next round: 300</h3' in str(resp.data))
            self.assertTrue(r'<h3>Activities to be started:</h3>\n    \n        '
                            r'<h4>A, Cost:\n            1800</h4>\n    \n        '
                            r'<h4>B, Cost:\n            600</h4>' in str(resp.data))

            # try invalid credit
            new_credit = 700
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post('/play', data=dict(
                csrf_token=csrf_resp,
                add_activity=routes.NONE_OPTION[0][0],
                remove_activity=routes.NONE_OPTION[0][0],
                apply_for_credit=new_credit,
                submit='Save'
            ), follow_redirects=True)

            self.assertTrue(r'<div class="alert alert-info" role="alert">'
                            r'Credit should be increment of 300</div>' in str(resp.data))
            self.assertTrue(r'<h3>Credit to be taken for next round: 300</h3' in str(resp.data))

            # try invalid credit again
            new_credit = 11000
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post('/play', data=dict(
                csrf_token=csrf_resp,
                add_activity=routes.NONE_OPTION[0][0],
                remove_activity=routes.NONE_OPTION[0][0],
                apply_for_credit=new_credit,
                submit='Save'
            ), follow_redirects=True)

            self.assertTrue(r'<div class="alert alert-info" role="alert">'
                            r'Credit should be increment of 300</div>\n            \n'
                            r'            <div class="alert alert-info" role="alert">'
                            r'Maximum size of credit is 9900</div>' in str(resp.data))

            new_credit = 600
            csrf_resp = self.get_csrf(resp)
            resp = self.client.post('/play', data=dict(
                csrf_token=csrf_resp,
                add_activity=routes.NONE_OPTION[0][0],
                remove_activity=team_act2.id,
                apply_for_credit=new_credit,
                submit='Save'
            ), follow_redirects=True)

            self.assertTrue(rf'<h3>Credit to be taken for next round: {new_credit}</h3'
                            in str(resp.data))
            self.assertTrue(r'<h3>Activities to be started:</h3>\n    \n        '
                            r'<h4>A, Cost:\n            1800</h4>' in str(resp.data))

            # increase period
            routes._calculate_next_period(game)
            game.increase_current_day(routes.PERIOD_INCREMENT_IN_DAYS)
            routes.commit_to_db(game)

            period_increment_in_days = 10
            days_in_game_month = 30
            credit_costs = routes.INTEREST_RATE_PER_MONTH * routes.STARTING_FUNDS * \
                (period_increment_in_days / days_in_game_month)
            available_funds = routes.STARTING_FUNDS - 1800 + new_credit - credit_costs
            resp = self.client.get('/play', follow_redirects=True)
            self.assertTrue(r'<h4>Credit costs: {0:.2f}</h4>'.format(credit_costs)
                            in str(resp.data))
            self.assertTrue(r'<h3>Credit total: 2700</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Available funds: {0:.2f}</h3>'.format(available_funds)
                            in str(resp.data))
            self.assertTrue(r'<h3>Credit to be taken for next round: 0</h3>' in str(resp.data))
            self.assertTrue(r'<h4>Penalties cost: 0</h4>' in str(resp.data))
            self.assertTrue(r'<h3>Activities finished:</h3>' in str(resp.data))
            self.assertTrue(r'<h3>Activities in progress:</h3>\n    \n        <h4>'
                            r'A - started on day 1,\n            Cost: 1800</h4>' in str(resp.data))

            # increase period
            new_credit_costs = routes.INTEREST_RATE_PER_MONTH *\
                2700 * period_increment_in_days / days_in_game_month
            new_available_funds = available_funds - new_credit_costs
            routes._calculate_next_period(game)
            game.increase_current_day(routes.PERIOD_INCREMENT_IN_DAYS)
            routes.commit_to_db(game)
            resp = self.client.get('/play', follow_redirects=True)
            self.assertTrue(r'<h4>Credit costs: {0:.2f}</h4>'.format(new_credit_costs))
            self.assertTrue(r'<h3>Available funds: {0:.2f}</h3>'.format(new_available_funds)
                            in str(resp.data))
            self.assertTrue(r'<h3>Activities finished:</h3>\n    \n        <h4>'
                            r'A - finished on day 21,\n            Cost: 1800</h4>' in str(resp.data))


if __name__ == '__main__':
    unittest.main()
