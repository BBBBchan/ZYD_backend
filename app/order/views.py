from flask import request, abort, jsonify, url_for, g, current_app

from app.middlewares import checkLogin
from app.models import Order, User, OrderExtra
from app.order import order_blueprint
from app.utils.serializers import serializer
from app.utils.utils import db_handler, set_value_from_request, push_message_to_user


@order_blueprint.route('/', methods=['POST'])
@checkLogin
def generate_user_order():
    data = request.json

    seller_id = data.get('seller_id')
    if seller_id is None:
        abort(400)
    try:
        new_order = Order(customer_id=g.user.id, seller_id=seller_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    db_handler(new_order)

    type = data.get('type')
    if type is None:
        abort(400)
    order_extra = OrderExtra(order=new_order)
    if type == 'shoot':
        set_value_from_request(new_order, data, ['time', 'content', 'thinking',
                                                 'requirements', 'is_take_deposit', 'customer_weixin'])
        set_value_from_request(order_extra, data, ['gender', 'age', 'location', 'late_protocol', 'is_solve_eat'])
    else:
        set_value_from_request(new_order, data, ['time', 'content', 'thinking',
                                                 'requirements', 'is_take_deposit', 'customer_weixin'])

    # 向设计师发送消息
    return jsonify({'id': new_order.id,
                    'detail_url': url_for('user_blueprint.get_user_order_detail',
                                          uid=new_order.id, _external=True)}), 200


@order_blueprint.route('/list/', methods=['GET'])
@checkLogin
def get_user_orders():
    if g.user.is_admin():
        # 如果当前用户为管理员，他具有查询用户订单的权限，而普通用户只能查看自己的订单
        uid = request.args.get('uid')
        if uid is None:
            abort(400)
        user = User.query.get_or_404(int(uid))
    else:
        user = g.user

    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    if user.is_designer() or user.is_super_designer():
        # 如果用户是设计师, 设计师接收的订单
        pagination = Order.query.filter_by(seller_id=user.id).order_by(Order.created_time.desc())\
            .order_by(Order.status).paginate(int(page_num), per_page=int(page_count), error_out=False)
    else:
        # 普通用户， 用户主动递交的订单
        pagination = Order.query.filter_by(customer_id=user.id).order_by(Order.created_time.desc())\
            .order_by(Order.status).paginate(int(page_num), per_page=int(page_count), error_out=False)

    orders = pagination.items
    data_set = []
    for order in orders:
        customer = User.query.get_or_404(order.customer_id).name
        seller = User.query.get_or_404(order.seller_id).name
        data = {'id': order.id,
                'customer': customer.name,
                'seller': seller.name,
                'customer_id': order.customer_id,
                'seller_id': order.seller_id,
                'status': order.status,
                'created_time': order.created_time,
                'detail_url': url_for('user_blueprint.get_user_order_detail', uid=order.id, _external=True)}
        data_set.append(data)
    return jsonify({'data': data_set, 'count': pagination.total, 'total_pages': pagination.pages}), 200


@order_blueprint.route('/<order_id>/', methods=['GET'])
@checkLogin
def get_user_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if g.user.id != order.seller_id and g.user.id != order.customer_id and not g.user.is_admin():
        # 只有买卖双方和管理员能看到他们的订单
        abort(403)
    order_extra = OrderExtra.filter_by(order_id=order_id).first()
    if order_extra is None:
        abort(404)
    data = serializer(order, ['id', 'customer_id', 'seller_id', 'status',
                              'created_time', 'time', 'content', 'requirements', 'thinking', 'is_take_deposit', 'type'])
    customer = User.query.get_or_404(order.customer_id).name
    seller = User.query.get_or_404(order.seller_id).name
    data.update({'customer': customer.name, 'seller': seller.name})

    if order_extra.type == 'shoot':
        extra_dict = serializer(order_extra, ['gender', 'age', 'location', 'late_protocol', 'is_solve_eat'])
        data.update(extra_dict)

    if g.user.is_designer() or g.user.is_super_designer():
        data.update({'customer_weixin': order.customer_weixin})
    return jsonify({'data': data}), 200


@order_blueprint.route('/confirm/<order_id>/', methods=['POST'])
@checkLogin
def confirm_user_order(order_id):
    # 是否接受订单
    is_agree = request.json.get('is_agree')
    if is_agree is None:
        abort(400)

    order = Order.query.get_or_404(order_id)
    if g.user.id != order.seller_id:
        # 若当前用户不是订单的卖家，则无法接受订单
        abort(403)
    if is_agree:
        order.status = 1
        content = '{seller}已接受您的订单'.format(seller=g.user.name)
    else:
        order.status = 2
        content = '{seller}拒绝了您的订单'.format(seller=g.user.name)
    push_message_to_user(order.customer_id, content)
    db_handler(order)
    return jsonify({'message': '操作成功'}), 200


@order_blueprint.route('/cancel/<order_id>/', methods=['GET'])
@checkLogin
def cancel_user_order(order_id):
    order = Order.query.get_or_404(order_id)
    if g.user.id != order.seller_id:
        # 若当前用户不是订单的卖家，则无法被取消
        abort(403)
    if order.status != 1:
        # 若当前订单未被接受, 则无法被取消
        abort(400)
    order.status = 2
    db_handler(order)
    # 向顾客发送消息
    push_message_to_user(order.customer_id, '您的订单被{seller}取消'.format(seller=g.user.name))
    return jsonify({'message': '操作成功'}), 200

