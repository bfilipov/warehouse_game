from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    faculty_number = StringField(_l('Faculty Number'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))

    #     def validate_email(self, email):
    #         match = User.query.filter_by(email=email.data).first()
    #         curr_user = self.meta.user
    #         if match and match != curr_user:
    #             raise ValidationError('Email is already taken.')

# class RegistrationForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('E-mail', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     repeat_password = PasswordField('Repeat Password',
#                                     validators=[DataRequired(), EqualTo('password')])
#
#     display_name = StringField('Display name', validators=[DataRequired()])
#
#     member1 = StringField('Student 1', validators=[DataRequired()])
#     member2 = StringField('Student 2')
#     member3 = StringField('Student 3')
#     member4 = StringField('Student 4')
#     member5 = StringField('Student 5')
#     member6 = StringField('Student 6')
#     member7 = StringField('Student 7')
#     member8 = StringField('Student 8')
#     member9 = StringField('Student 9')
#     member10 = StringField('Student 10')
#
#     submit = SubmitField('Register')
#
#     def validate_username(self, username):
#         user = User.query.filter_by(username=username.data).first()
#         if user is not None:
#             raise ValidationError('Username is already taken.')
#
#     def validate_display_name(self, display_name):
#         user = User.query.filter_by(display_name=display_name.data).first()
#         if user is not None:
#             raise ValidationError('Display name is already taken.')
#
#     def validate_email(self, email):
#         user = User.query.filter_by(email=email.data).first()
#         if user is not None:
#             raise ValidationError('Email is already taken.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))
