from datetime import datetime
from hashlib import md5
from time import time

from flask import current_app
from flask_login import UserMixin
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app import login

INITAL_CREDIT_AMOUNT = 2000


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, index=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class User(UserMixin, BaseModel):
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_superadmin = db.Column(db.Boolean, default=False)
    is_manager = db.Column(db.Boolean, default=False)
    is_cashier = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(64), index=True, unique=True)
    display_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    faculty_number = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(120))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


class Team(BaseModel):
    inputs = db.relationship('Input', backref='team', lazy='dynamic')
    display_name = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    users = db.relationship('User', backref='team', lazy='dynamic')
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))


class Game(BaseModel):
    current_day = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    teams = db.relationship('Team', backref='game', lazy='dynamic')

    def increase_current_day(self, days):
        self.current_day += days

    def decrease_current_day(self, days):
        new_day = self.current_day - days
        if new_day <= 0:
            new_day = 1
        self.current_day = new_day


class Settings(BaseModel):
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), unique=True)


class Input(BaseModel):
    # id in format: 'team_id'_'current_day'
    id = db.Column(db.String(64), primary_key=True, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    credit_taken = db.Column(db.Integer, default=0)
    credit_to_take = db.Column(db.Integer, default=0)
    activities = db.relationship('TeamActivity', backref='input', lazy='dynamic')

    penalties = db.relationship('Penalty', backref='input', lazy='dynamic')
    interest_cost = db.Column(db.Float, default=0)
    total_penalty_cost = db.Column(db.Float, default=0)
    rent_cost = db.Column(db.Integer, default=0)

    # period_id = db.Column(db.String(64), db.ForeignKey('period.id'))
    active_at_day = db.Column(db.Integer)
    money_at_start_of_period = db.Column(db.Float, default=0)
    money_at_end_of_period = db.Column(db.Float, default=0)
    approved_by_admin = db.Column(db.Boolean, default=False)


class Penalty(BaseModel):
    input_id = db.Column(db.String, db.ForeignKey('input.id'))
    activity_id = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))
    fine = db.Column(db.Integer, default=60)


class InputHistory(BaseModel):
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    current_day = db.Column(db.Integer, default=0)
    activity_to_add = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))
    activity_to_remove = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))
    credit_to_take = db.Column(db.Integer)


class Activity(BaseModel):
    id = db.Column(db.String(64), primary_key=True, index=True, onupdate="cascade")
    title = db.Column(db.Text())
    description = db.Column(db.Text())
    days_needed = db.Column(db.Integer, default=1)
    cost = db.Column(db.Integer, default=100)


class TeamActivity(BaseModel):
    id = db.Column(db.String(64), primary_key=True, index=True)
    team = db.Column(db.Integer, db.ForeignKey('team.id'))
    game = db.Column(db.Integer, db.ForeignKey('game.id'))
    activity_id = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))
    cost = db.Column(db.Integer, default=100)  # add penalties here?
    input_id = db.Column(db.String(64), db.ForeignKey('input.id', ondelete="CASCADE"))
    started_on_day = db.Column(db.Integer, default=0)
    finished_on_day = db.Column(db.Integer, default=0)
    initiated_on_day = db.Column(db.Integer, default=0)
    first_time_ever_initiated_on_day = db.Column(db.Integer, default=0)


class ActivityRequirement(BaseModel):
    # id = db.Column(db.Integer , primary_key=True , autoincrement=True)
    activity_id = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))
    requirement_id = db.Column(db.String(64), db.ForeignKey('activity.id', ondelete="cascade"))


# class Period(BaseModel):
#     id = db.Column(db.String(64), primary_key=True, index=True)
#     game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
#     team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
#     period_number = db.Column(db.Integer)
#     input_id = db.relationship('Input', backref='period', lazy='dynamic')
