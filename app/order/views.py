import time

from flask import Blueprint, request, abort, jsonify

from app.config import logger
from app.middlewares import checkLogin
from app.models import Order, User
from app.utils.serializers import serializer
from app.utils.utils import db_handler

order_blueprint = Blueprint('order_blueprint', __name__)


@order_blueprint.route('/', methods=['POST'])
@checkLogin
def generate_user_order():
    data = request.json
    try:
        requirements = data['requirements']
        seller_id = data['seller_id']
        all_price = data['all_price']
    except Exception as e:
        logger.error(e)
        abort(400)
    '''
    获得总价
    services = json.loads(requirements)
    all_price = 0
    for k, v in services.items():
        all_price += v
    '''
    # 生成order_id --> 用户订单号
    prefix = str(round(time.time() * 1000))
    salt = '{c_id}{s_id}'.format(c_id=g.user.id, s_id=seller_id)
    order_id = prefix + salt
    try:
        new_order = Order(order_id=order_id, customer_id=g.user.id, seller_id=seller_id, requirements=requirements,
                          all_price=all_price, status=0)
    except Exception as e:
        logger.error(e)
        abort(500)
    db_handler(new_order)
    # 向设计师发生消息
    return jsonify({'id': new_order.id}), 200


@order_blueprint.route('/list/', methods=['GET'])
@checkLogin
def get_user_orders():
    user = g.user
    if user.is_designer() or user.is_super_designer():
        # 如果用户是设计师, 设计师接收的订单
        orders = Order.query.filter_by(seller_id=user.id).order_by(Order.created_time.desc())
    else:
        # 普通用户， 用户主动递交的订单
        orders = Order.query.filter_by(customer_id=user.id).order_by(Order.created_time.desc())

    data_set = []
    for order in orders:
        customer = User.query.get_or_404(order.customer_id).name
        seller = User.query.get_or_404(order.seller_id).name
        data = {'id': order.id,
                'customer': customer,
                'seller': seller,
                'customer_id': order.customer_id,
                'seller_id': order.seller_id,
                'order_id': order.order_id,
                'requirements': order.requirements,
                'all_price': str(order.all_price),
                'status': order.status,
                'created_time': order.created_time}
        data_set.append(data)
    return jsonify({'data': data_set}), 200


@order_blueprint.route('/<order_id>/', methods=['GET'])
@checkLogin
def get_user_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    data = serializer(order, ['id', 'customer_id', 'seller_id', 'requirements', 'order_id', 'status', 'created_time'])
    customer = User.query.get_or_404(order.customer_id).name
    seller = User.query.get_or_404(order.seller_id).name
    data.update({'customer': customer, 'seller': seller, 'all_price': str(order.all_price)})
    return jsonify({'data': data}), 200


@order_blueprint.route('/confirm/<order_id>/', methods=['GET'])
@checkLogin
def confirm_user_order(order_id):
    # 是否接受订单
    is_agree = request.json.get('is_agree')
    if is_agree is None:
        abort(400)
    if is_agree:
        order = Order.query.get_or_404(order_id)
        order.status = 1
        db_handler(order)
        # 向顾客发送成功消息
    else:
        # 向顾客发生失败消息
        pass
    return jsonify({'message': '操作成功'}), 200
