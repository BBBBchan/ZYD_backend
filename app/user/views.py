import datetime
import json

from flask import Blueprint, request, jsonify, abort, g

from app.middlewares import checkLogin
from app.models import User, db, ReportMessage, ApplyMessage
from app.utils.serializers import serializer, save_or_not
from app.utils.utils import upload_avatar, upload_avatar_v1
from app.utils.wx_api import get_session_key_and_openid, generate_3rd_session, update_token, redis_service

user_blueprint = Blueprint('user_blueprint', __name__)


@user_blueprint.route('/login/', methods=['POST'])
def login():
    data = request.json

    try:
        code = data['code']
    except:
        abort(400)

    session_key, openid = get_session_key_and_openid(code)

    try:
        user = User.query.filter_by(openid=openid).first()
    except:
        user = None

    if not user:
        # user为空，说明为新用户，获取其信息录入数据库
        try:
            name = data['nickName']
            avatar = request.files['avatar']
            url = upload_avatar_v1(avatar)
            user = User(openid=openid, name=name, avatarUrl=url)
            db.session.add(user)
            db.session.commit()
            # 让用户成为他自己的粉丝
            db.session.add(user.follow(user))
            db.session.commit()
        except:
            abort(500)

    token = generate_3rd_session(session_key, openid)

    return jsonify({'token': token, 'uid': user.id}), 200


@user_blueprint.route('/token/', methods=['GET'])
def generate_new_token():
    """
    更新用户token
    """
    token = request.headers['Authorization']
    if not token:
        abort(400)
    new_token = update_token(token)
    return jsonify({'token': new_token}), 200


@user_blueprint.route('/<uid>/', methods=['GET'])
def get_user_info(uid):
    user = User.query.get_or_404(uid)

    extra_dict = {
        'followed': '/user/followed/list/',
        'followers': '/user/followers/list/',
        'works': '/picture/list/',
        'showcases': '/showcase/list/',
        'orders': '/order/list/'
    }

    if user.is_designer():
        data = serializer(user, ['id', 'name', 'avatarUrl', 'tag', 'pricing', 'last_login', 'role'], extra_dict)
    else:
        data = serializer(user, ['id', 'name', 'avatarUrl', 'last_login', 'role'], extra_dict)
    return jsonify({'data': data}), 200


@user_blueprint.route('/', methods=['POST'])
@checkLogin
def change_user_info():
    data = request.json
    user = g.user
    if user.is_designer():
        save_or_not(user, ['name', 'tag', 'pricing'], data)
    else:
        save_or_not(user, ['name'], data)
    return jsonify({'msg': 'OK', 'uid': user.id}), 200


@user_blueprint.route('/avatar_v1/', methods=['POST'])
def avatar_v1():
    """
    保存图片至服务器
    """
    try:
        avatar = request.files['avatar']
    except:
        abort(400)
    g.user.avatarUrl = upload_avatar_v1(avatar)
    g.session.add(g.user)
    g.session.commit()
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/avatar/', methods=['POST'])
@checkLogin
def change_avatar():
    """
    保存图片至图床
    """
    try:
        avatar = request.files['avatar']
    except:
        abort(400)
    try:
        url = upload_avatar(avatar.read())
    except:
        abort(500)
    try:
        g.user.avatarUrl = url
        db.session.add(g.user)
        db.session.commit()
    except:
        abort(500)

    return jsonify({'avatarUrl': url}), 200


@user_blueprint.route('/relationship/<uid>/', methods=['GET'])
@checkLogin
def follow(uid):
    received_user = User.query.get_or_404(uid)
    if g.user.is_following(received_user):
        g.user.unfollow(received_user)
    else:
        g.user.follow(received_user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/followed/list/', methods=['GET'])
@checkLogin
def followed_list():
    followed_user_list = g.user.followed.all()
    data = [serializer(f, ['id', 'name', 'avatarUrl']) for f in followed_user_list]
    return jsonify({'data': data}), 200


@user_blueprint.route('/followers/list/', methods=['GET'])
@checkLogin
def followers_list():
    followers = g.user.followers.all()
    data = [serializer(f, ['id', 'name', 'avatarUrl']) for f in followers]
    return jsonify({'data': data}), 200


"""
@user_blueprint.route('/auto_report/<uid>/', methods=['GET'])
@checkLogin
def auto_report(uid):
    user = User.query.get_or_404(uid)
    count = redis_service.incr('report-' + str(user.id))
    if count > 3:
        user.is_banned = True
        db.session.add(user)
        db.session.commit()
    return jsonify({'msg': 'OK'}), 200
"""


@user_blueprint.route('/report/<uid>/', methods=['POST'])
@checkLogin
def report(uid):
    try:
        reason = request.json['reason']
    except:
        abort(400)
    reported_user = User.query.get_or_404(uid)
    try:
        report_message = ReportMessage(reason=reason, reported=reported_user, reporter=g.user)
        db.session.add(report_message)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e}), 500
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/apply/', methods=['GET'])
@checkLogin
def apply():
    try:
        detail = request.json['detail']
    except:
        abort(400)
    user = g.user
    if user.is_designer():
        apply_type = '特约设计师'
    elif not user.is_super_designer():
        apply_type = '设计师'
    else:
        return jsonify({'error': '您已经是特约设计师了，无需再进行申请'}), 404
    try:
        apply_message = ApplyMessage(applicant=user, detail=detail)
        db.session.add(apply_message)
        db.session.commit()
    except Exception as e:
        return jsonify({'error': e}), 500
    return jsonify({'msg': 'OK'}), 200
