from flask import Flask, url_for, render_template, request, flash, redirect
from config import DevelopmentConfig
import redis
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user

app = Flask(__name__)
app.config.from_object(DevelopmentConfig())
redis_cli = redis.StrictRedis(**app.config['REDIS_CONF'])
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User(user_id).retrieve_user_by_id()


class User(UserMixin):
    def __init__(self, user_id=-1):
        self.username = ''
        self.id = user_id
        self.password_hash = ''

    def register(self, username, password):
        self.username = username
        if redis_cli.hget('user:index', self.username):
            return False
        self.id = redis_cli.incr('user:id')
        redis_cli.hset('user:index', self.username, self.id)  # 会和hget冲突，需锁或watch
        self.set_password(password)
        redis_cli.hmset(f'user:info:{self.id}', {'name': self.username, 'password': self.password_hash})
        return True

    def retrieve_user(self, username):
        self.username = username
        self.id = redis_cli.hget('user:index', self.username)
        if not self.id:
            return False
        user = redis_cli.hgetall(f'user:info:{self.id}')
        self.password_hash = user['password']
        return self

    def retrieve_user_by_id(self):
        user = redis_cli.hgetall(f'user:info:{self.id}')
        if not user:
            return False
        self.username = user['name']
        self.password_hash = user['password']
        return self

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route('/')
def index():
    top_discount = redis_cli.zrange('discount:highest', 0, 41, desc=True, withscores=True)
    products = []
    for product_id, score in top_discount:
        product = redis_cli.hgetall(f'item:info:{product_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    products = [products[i:i+3] for i in range(0, len(products), 3)]
    return render_template('index.html', products=products)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    username = request.form['username']
    password = request.form['password']
    if not User().register(username, password):
        flash('Please try another username.')
        return redirect(url_for('signup'))
    else:
        flash('Success! Please login.')
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['username']
    password = request.form['password']
    user = User().retrieve_user(username)
    if user and user.validate_password(password):
        login_user(user)
        print(current_user, current_user.id)
        flash('Login success.')
        return redirect(url_for('index'))
    flash('Invalid username or password')
    return redirect(url_for('login'))


@app.route('/like/<int:user_id>/<int:item_id>')
def like(user_id, item_id):
    if not redis_cli.sadd(f'user:like:{user_id}', item_id):
        flash('You already liked.')
    else:
        redis_cli.zincrby('like:count', 1, item_id)
    return redirect(request.referrer)


@app.route('/star/<int:user_id>/<int:item_id>')
def star(user_id, item_id):
    if not redis_cli.sadd(f'user:star:{user_id}', item_id):
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


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_content = str(request.form['search_content']).lower()
    search_item_ids = redis_cli.smembers(f'{search_content}:items')
    search_res = []
    for item_id in search_item_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        search_res.append(product)
    num_items = len(search_res)
    search_res = [search_res[i:i+3] for i in range(0, len(search_res), 3)]
    return render_template('search.html', search_res=search_res, num=num_items)


@app.route('/auto-completion', methods=['GET', 'POST'])
def auto_completion():
    search_content = str(request.form['search_content']).lower()
    search_res = redis_cli.zrangebylex('brands:', '['+search_content, '('+search_content+'{')
    print(search_res)
    return render_template('search.html', search_res=search_res)
