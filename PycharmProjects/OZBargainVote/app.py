from flask import Flask, escape, url_for, render_template, request, flash, redirect
from config import DevelopmentConfig
import redis

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
redis_cli = redis.StrictRedis(**app.config['REDIS_CONF'])


class User:
    def __init__(self, name):
        user_id = redis_cli.incr('user:id')
        redis_cli.hmset('user:' + str(user_id), {'name': name})


class Movie:
    def __init__(self, user_id, title, author):
        movie_id = redis_cli.incr('movie:id')
        redis_cli.hmset('movie:' + str(movie_id), {'title': title, 'author': author})
        redis_cli.sadd('user'+str(user_id)+':movie', title)


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

    title = request.form.get('title')
    author = request.form.get('author')
    if len(title) == 1:
        flash('Invalid input')
        return redirect(url_for('index'))
    Movie(3, title, author)
    flash('Item added')
    return redirect(url_for('index'))
