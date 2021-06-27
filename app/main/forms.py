from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, NumberRange

from app.models import User


class TeamAssign(FlaskForm):
    user = SelectField('Player', validators=[DataRequired()])
    submit = SubmitField('Add')


class UserForm(FlaskForm):
    is_manager = BooleanField('is_manager', validators=[])
    is_cashier = BooleanField('is_cashier', validators=[])
    username = StringField('username', validators=[DataRequired()])
    display_name = StringField('display_name', validators=[DataRequired()])
    # email = StringField('display_name', validators=[DataRequired()])
    faculty_number = StringField('faculty_number', validators=[DataRequired()])
    team_id = SelectField('Team', validators=[DataRequired()])
    submit = SubmitField('Save')
