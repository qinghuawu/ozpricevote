from flask import Flask, url_for, render_template, request, flash, redirect, make_response, session
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
import redis
import json
from config import Config
from model import User
from forms import SignupForm, LoginForm

app = Flask(__name__)
app.config.from_object(Config())
redis_cli = redis.StrictRedis(**app.config['REDIS_CONF'])
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User(user_id).retrieve_user_by_id()


@app.route('/')
def index():
    top_discount = redis_cli.zrange('discount:highest', 0, 41, desc=True, withscores=True)
    products = []
    for product_id, score in top_discount:
        product = redis_cli.hgetall(f'item:info:{product_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    products = [products[i:i + 3] for i in range(0, len(products), 3)]
    return render_template('index.html', products=products)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if not User().register(username, password):
            flash('Please try another username.')
            return redirect(url_for('signup'))
        flash('Success! Please login.')
        return redirect(url_for('login'))
    return render_template('signup_login.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User().retrieve_user(username)
        if user and user.validate_password(password):
            login_user(user)
            print(current_user, current_user.id)
            flash('Login success.')
            return redirect(url_for('index'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('signup_login.html', form=form)


@app.route('/like/<int:item_id>', methods=['POST'])
@login_required
def like(item_id):
    if not redis_cli.sadd(f'user:like:{current_user.id}', item_id):
        flash('You already liked.')
    else:
        redis_cli.zincrby('like:count', 1, item_id)
    return redirect(request.referrer)


@app.route('/star/<int:item_id>', methods=['POST'])
@login_required
def star(item_id):
    if not redis_cli.sadd(f'user:star:{current_user.id}', item_id):
        flash('You already starred.')
    return redirect(request.referrer)


@app.route('/like_board')
def like_board():
    top_products = redis_cli.zrange('like:count', 0, 9, desc=True, withscores=True)
    product_info = []
    for product_id, score in top_products:
        product = redis_cli.hgetall(f'item:info:{product_id}')
        product['like_count'] = int(score)
        product_info.append(product)
    return render_template('like_board.html', product_info=product_info)


@app.route('/discount_board')
def discount_board():
    lowest_in_history = []
    item_id_list = redis_cli.srandmember('price:lowest_history', 54)
    for item_id in item_id_list:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        lowest_in_history.append(product)
    lowest_in_history = [lowest_in_history[i:i + 3] for i in range(0, len(lowest_in_history), 3)]
    return render_template('discount_board.html', products=lowest_in_history)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successfully.')
    return redirect(url_for('index'))


@app.route('/user_space')
def user_space():
    return render_template('user_space.html')


@app.route('/my_like')
def my_like():
    like_product_ids = redis_cli.smembers(f'user:like:{current_user.id}')
    products = []
    for item_id in like_product_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    return render_template('my_like.html', products=products)


@app.route('/cancel_like/<int:item_id>')
def cancel_like(item_id):
    redis_cli.srem(f'user:like:{current_user.id}', item_id)
    redis_cli.zincrby('like:count', -1, item_id)
    return redirect(url_for('my_like'))


@app.route('/my_collection')
def my_collection():
    star_product_ids = redis_cli.smembers(f'user:star:{current_user.id}')
    products = []
    for item_id in star_product_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    return render_template('my_collection.html', products=products)


@app.route('/cancel_star/<int:item_id>')
def cancel_star(item_id):
    redis_cli.srem(f'user:star:{current_user.id}', item_id)
    return redirect(url_for('my_collection'))


@app.route('/search')
def search():
    search_content = str(request.args['search_content']).lower()
    search_item_ids = redis_cli.smembers(f'{search_content}:items')
    search_res = []
    for item_id in search_item_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        search_res.append(product)
    num_items = len(search_res)
    search_res = [search_res[i:i + 3] for i in range(0, len(search_res), 3)]
    return render_template('search.html', search_res=search_res, num=num_items)


@app.route('/autocomplete')
def autocomplete():
    completion_content = str(request.args.get('term')).lower()
    completion_res = redis_cli.zrangebylex('brands:', '[' + completion_content, '(' + completion_content + '{')[:8]
    return json.dumps(completion_res)
