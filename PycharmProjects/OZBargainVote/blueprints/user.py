from flask import render_template, Blueprint
from flask_login import login_required, current_user
from model import redis_cli

user_bp = Blueprint('user', __name__)


@user_bp.route('/my-space')
def user_space():
    return render_template('_user_space.html')


@user_bp.route('/my-like')
@login_required
def my_like():
    like_product_ids = redis_cli.smembers(f'user:like:{current_user.id}')
    products = []
    for item_id in like_product_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    return render_template('_my_like.html', products=products)


@user_bp.route('/my-collection')
@login_required
def my_collection():
    star_product_ids = redis_cli.smembers(f'user:star:{current_user.id}')
    products = []
    for item_id in star_product_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    return render_template('_my_collection.html', products=products)
