from flask import Flask, url_for, render_template, request, flash, redirect
from config import DevelopmentConfig
import redis
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
redis_cli = redis.StrictRedis(**app.config['REDIS_CONF'])
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User(user_id).retrieve_user()


class User(UserMixin):
    def __init__(self, user_name):
        self.password_hash = ''
        self.id = user_name
        self.id_seq = -1

    def register(self, password):
        self.set_password(password)
        self.id_seq = redis_cli.incr('user:id')
        redis_cli.hmset(f'user:{self.id}', {'id_seq': self.id_seq, 'password': self.password_hash})

    def retrieve_user(self):
        user = redis_cli.hgetall(f'user:{self.id}')
        if not user:
            return None
        self.password_hash = user['password']
        self.id_seq = user['id_seq']
        return self

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Movie:
    def __init__(self, user_id, title, author):
        movie_id = redis_cli.incr('movie:id')
        redis_cli.hmset('movie:' + str(movie_id), {'title': title, 'author': author})
        redis_cli.sadd('user' + str(user_id) + ':movie', title)


# movies = [
#     {'title': 'My Neighbor Totoro', 'year': '1988'},
#     {'title': 'Dead Poets Society', 'year': '1989'},
#     {'title': 'A Perfect World', 'year': '1993'},
#     {'title': 'Leon', 'year': '1994'},
#     {'title': 'Mahjong', 'year': '1996'},
#     {'title': 'Swallowtail Butterfly', 'year': '1996'},
#     {'title': 'King of Comedy', 'year': '1999'},
#     {'title': 'Devils on the Doorstep', 'year': '1999'},
#     {'title': 'WALL-E', 'year': '2008'},
#     {'title': 'The Pork of Music', 'year': '2012'},
# ]

name = 'wqh'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        movies = redis_cli.smembers('user3:movie')
        return render_template('index.html', name=name, movies=movies)

    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    title = request.form.get('title')
    author = request.form.get('author')
    if len(title) == 1:
        flash('Invalid input')
        return redirect(url_for('index'))
    Movie(3, title, author)
    flash('Item added')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', name=name)
    user_name = request.form['username']
    password = request.form['password']
    user = User(user_name).retrieve_user()
    if user and user.validate_password(password):
        login_user(user)
        flash('Login success.')
        return redirect(url_for('index'))
    flash('Invalid username or password')
    return redirect(url_for('login'))


@app.route('/movie/delete/<movie_id>', methods=['POST'])
def delete(movie_id):
    flash(f'{movie_id} deleted')
    return redirect(url_for('index'))
