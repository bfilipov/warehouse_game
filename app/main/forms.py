from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, \
    RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange, Optional

from app.models import User


class TeamAssign(FlaskForm):
    is_active = BooleanField('Is Active?', validators=[])
    user = SelectField('Player', validators=[Optional()])
    submit = SubmitField('Save')


class UserForm(FlaskForm):
    is_manager = BooleanField('is_manager', validators=[])
    is_cashier = BooleanField('is_cashier', validators=[])
    username = StringField('username', validators=[DataRequired()])
    display_name = StringField('display_name', validators=[DataRequired()])
    # email = StringField('display_name', validators=[DataRequired()])
    faculty_number = StringField('faculty_number', validators=[DataRequired()])
    team_id = SelectField('Team', validators=[DataRequired()])
    submit = SubmitField('Save')


class GameAssignForm(FlaskForm):
    team = SelectField('Add Team', validators=[DataRequired()])
    submit = SubmitField('Add')


class GameCreateForm(FlaskForm):
    submit = SubmitField('New Game')


class GamePlayForm(FlaskForm):
    increase_period = RadioField('Label', choices=[('increase', 'Increase period'), ('decrease', 'Decrease period')])
    submit = SubmitField('Save')


class GameUserForm(FlaskForm):
    activity = SelectField('Add activity', validators=[Optional()])
    remove_activity = SelectField('Remove activity', validators=[Optional()])
    submit = SubmitField('Save')
