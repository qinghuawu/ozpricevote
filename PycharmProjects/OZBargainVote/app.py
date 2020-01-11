from flask import Flask, escape

app = Flask(__name__)


@app.route('/')
def hello():
    return 'Welcome to My Watchlist!'

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'
