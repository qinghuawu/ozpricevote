from flask import render_template, Blueprint, redirect, url_for, jsonify, request
from flask_login import login_user, current_user, login_required, logout_user
from model import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home.discount'))

    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        if not User().register(username, password):
            return jsonify(message='Signup failed. Please retry.'), 400
        return jsonify(message='Signup success. Please login.')
    return render_template('_signup_login.html', mode='signup')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.discount'))

    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        user = User().retrieve_user(username)
        if user and user.validate_password(password):
            login_user(user)
            return jsonify(message='Login success.')
        return jsonify(message='Invalid username or password.'), 400
    return render_template('_signup_login.html', mode='login')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify(message='Logout success.')
