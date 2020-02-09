from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class SLForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], id='username-input')
    password = PasswordField('Password', validators=[DataRequired()], id='password-input')
    remember = BooleanField('Remember me')


class SignupForm(SLForm):
    _name = 'Signup'
    submit = SubmitField('Sign up', render_kw={'class': 'btn'}, id='signup-btn')


class LoginForm(SLForm):
    _name = 'Login'
    submit = SubmitField('Login', render_kw={'class': 'btn'}, id='login-btn')
