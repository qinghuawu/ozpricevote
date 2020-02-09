from flask import render_template, Blueprint, request, jsonify, redirect
from model import redis_cli

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
def index():
    if request.args:
        search_content = str(request.args['search_content']).lower()
        search_item_ids = redis_cli.smembers(f'{search_content}:items')
        search_res = []
        for item_id in search_item_ids:
            product = redis_cli.hgetall(f'item:info:{item_id}')
            product['discount'] = str(round(float(product['discount']) * 100)) + '%'
            search_res.append(product)
        num_items = len(search_res)
        search_res = [search_res[i:i + 3] for i in range(0, len(search_res), 3)]
        return render_template('_search.html', search_res=search_res, num=num_items)
    return render_template('index.html')


@home_bp.route('/discount')
def discount():
    top_discount = redis_cli.zrange('discount:highest', 0, 35, desc=True, withscores=True)
    products = []
    for product_id, score in top_discount:
        product = redis_cli.hgetall(f'item:info:{product_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        products.append(product)
    products = [products[i:i + 3] for i in range(0, len(products), 3)]
    return render_template('_discount.html', products=products)


@home_bp.route('/cheapest-in-history')
def cheapest():
    cheapest_in_history = []
    item_id_list = redis_cli.srandmember('price:lowest_history', 36)
    for item_id in item_id_list:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        cheapest_in_history.append(product)
    cheapest_in_history = [cheapest_in_history[i:i + 3] for i in range(0, len(cheapest_in_history), 3)]
    return render_template('_cheapest_in_history.html', products=cheapest_in_history)


@home_bp.route('/like-chart')
def like_chart():
    top_products = redis_cli.zrange('like:count', 0, 9, desc=True, withscores=True)
    product_info = []
    for product_id, score in top_products:
        product = redis_cli.hgetall(f'item:info:{product_id}')
        product['like_count'] = int(score)
        product_info.append(product)
    return render_template('_like_chart.html', product_info=product_info)


@home_bp.route('/autocomplete')
def autocomplete():
    completion_content = str(request.args.get('term')).lower()
    completion_res = redis_cli.zrangebylex('brands:', '[' + completion_content, '(' + completion_content + '{')[:8]
    return jsonify(completion_res)


@home_bp.route('/brands', methods=['POST'])
def search():
    search_content = request.get_json()['search_content'].lower()
    search_item_ids = redis_cli.smembers(f'{search_content}:items')
    search_res = []
    for item_id in search_item_ids:
        product = redis_cli.hgetall(f'item:info:{item_id}')
        product['discount'] = str(round(float(product['discount']) * 100)) + '%'
        search_res.append(product)
    num_items = len(search_res)
    search_res = [search_res[i:i + 3] for i in range(0, len(search_res), 3)]
    return jsonify(html=render_template('_search.html', search_res=search_res, num=num_items))
