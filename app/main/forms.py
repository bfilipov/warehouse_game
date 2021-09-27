from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, \
    RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange, Optional

from app.models import User


class TeamAssign(FlaskForm):
    is_active = BooleanField('Is Active?', validators=[])
    add_user = SelectField('Add player', validators=[Optional()])
    remove_user = SelectField('Remove player', validators=[Optional()])
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


class TeamForm(FlaskForm):
    display_name = StringField('Add new team', validators=[DataRequired()])
    submit = SubmitField('Add')


class GameAssignForm(FlaskForm):
    add_team = SelectField('Add Team', validators=[DataRequired()])
    remove_team = SelectField('Remove Team', validators=[DataRequired()])
    submit = SubmitField('Save')


class GameCreateForm(FlaskForm):
    submit = SubmitField('New Game')


class GamePlayForm(FlaskForm):
    increase_period = RadioField('Label', choices=[('increase', 'Increase period'), ('decrease', 'Decrease period')])
    submit = SubmitField('Save')


class GameUserForm(FlaskForm):
    add_activity = SelectField('Add activity', validators=[Optional()])
    remove_activity = SelectField('Remove activity', validators=[Optional()])
    apply_for_credit = IntegerField('Apply for credit', validators=[Optional()])

    submit = SubmitField('Save')
