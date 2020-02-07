from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class SLForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')


class SignupForm(SLForm):
    _name = 'Signup'
    submit = SubmitField('Sign up', render_kw={'class': 'btn'})


class LoginForm(SLForm):
    _name = 'Login'
    submit = SubmitField('Login', render_kw={'class': 'btn'})
