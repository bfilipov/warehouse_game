from datetime import datetime
from hashlib import md5

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app import login


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, index=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class User(UserMixin, BaseModel):
    is_admin = db.Column(db.Boolean, default=False)
    is_manager = db.Column(db.Boolean, default=False)
    is_cashier = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(64), index=True, unique=True)
    display_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    faculty_number = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(120))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


class Team(BaseModel):
    input = db.relationship('Input', backref='team', lazy='dynamic')
    users = db.relationship('User', backref='team', lazy='dynamic')
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))


class Game(BaseModel):
    current_day = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    teams = db.relationship('Team', backref='game', lazy='dynamic')


class Settings(BaseModel):
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), unique=True)


class Input(BaseModel):
    id = db.Column(db.String(64), primary_key=True, index=True)
    credit = db.Column(db.Integer, default=0)
    # activities = db.relationship('Activity', backref='input', lazy='dynamic')
    activities = db.Column(db.ARRAY(db.Integer))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    approved_by_admin = db.Column(db.Boolean, default=False)


class Activity(BaseModel):
    name = db.Column(db.String(64))
    description = db.Column(db.Text())
    is_completed = db.Column(db.Boolean, default=False)
    is_started = db.Column(db.Boolean, default=False)
    days_needed = db.Column(db.Integer, default=1)
    requirements = db.Column(db.ARRAY(db.Integer))


class Period(BaseModel):
    id = db.Column(db.String(64), primary_key=True, index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    period_number = db.Column(db.Integer)
    input_id = db.Column(db.String(64), db.ForeignKey('input.id'))  # USER INPUIT


# def autoregister_users(file_path):
#     with open(file_path) as f:
#         for line in f:
#             username, display_name, email, raw_pass = line.split()
#
#             # TODO:!!!REMOVE THE BEWLOW PDB BREAKPOINT
#             import ipdb; ipdb.set_trace()
#             # TODO:!!!REMOVE THE ABOVE PDB BREAKPOINT

    # ------------------

    # # custom commands
    # # add default admin
    # op.execute("INSERT INTO \"user\" (id, is_admin, username, display_name, email, password_hash) "
    #            "VALUES (default, TRUE, 'admin', 'админ', 'filipov.bogomil@gmal.com', "
    #            "'pbkdf2:sha256:150000$4cxvcwnI$dd8e2193d11aed58163e6e2fbe57283cf69cb3dd"
    #            "af24dec0b4ae8b579112bf29');")
    #
    # # populate products
    # for product in [(1, 'Обикновено'), (2, 'Уелнес'), (3, 'Лукс')]:
    #     op.execute(f"INSERT INTO \"product\" (id, name) VALUES ({product[0]}, '{product[1]}');")
    #
    # # populate scenario per product
    # for product in [1, 2, 3]:
    #     cost_materials = product + 2
    #
    #     for period in range(1, 21):
    #         cost_unpredicted = 0
    #
    #         op.execute('INSERT INTO "scenario_per_product" (id, demand_scenario_id, period, product_id, '
    #                    'demand_quantity, sensitivity_price, sensitivity_quality, sensitivity_marketing, '
    #                    'correction_cost_labor, correction_cost_materials_for_one_product, '
    #                    'cost_unpredicted, cost_materials_for_one_product, cost_labor, investment_for_one_marketing, '
    #                    'investment_for_one_quality, quality_index_min, quality_index_max, marketing_index_min, '
    #                    'marketing_index_max, marketing_keep_effect, base_value_rand_quality, cost_transport, '
    #                    'cost_storage, cost_product_manager, cost_new_product_manager, price_research, max_price) '
    #                    f'VALUES (default, 1, {period}, {product}, 3850, 1, 1.05, 0.95, 1, 1, {cost_unpredicted}, '
    #                    f'{cost_materials}, 5, 200, 1000, 2, 5, 2, 5, 0.5, 0.7, 1.5, 0.5, 1000, 1500, 500, 50);')
    #
    # # populate scenario per period
    # for period in range(1, 21):
    #     op.execute('INSERT INTO "scenario_per_period" (id, demand_scenario_id, period, cost_fixed_administrative, '
    #                'interest_credit, interest_overdraft) '
    #                f'VALUES (default, 1, {period}, 5000, 0.05, 0.1);')
    # # ### end Alembic commands ###
