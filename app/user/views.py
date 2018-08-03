import datetime
import json

from flask import Blueprint, request, jsonify, abort, g

from app.middlewares import checkLogin
from app.models import User, db
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
    if user.is_designer():
        data = serializer(user, ['name', 'avatarUrl', 'tag', 'pricing'])
    else:
        data = serializer(user, ['name', 'avatarUrl'])
    return jsonify(data), 200


@user_blueprint.route('/', methods=['POST'])
@checkLogin
def change_user_info():
    data = request.json
    user = g.user
    if user.is_designer():
        save_or_not(user, ['name', 'tag', 'pricing'], data)
    else:
        save_or_not(user, ['name'], data)
    return jsonify({'uid': user.id}), 200


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


@user_blueprint.route('/follow/<uid>/', methods=['GET'])
@checkLogin
def follow(uid):
    followed_user = User.query.get_or_404(uid)
    g.user.follow(followed_user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/unfollow/<uid>/', methods=['GET'])
@checkLogin
def unfollow(uid):
    followed_user = User.query.get_or_404(uid)
    g.user.unfollow(followed_user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/followed/list/', methods=['GET'])
@checkLogin
def followed_list():
    followed_user_list = g.user.followed.all()
    data = [serializer(f, ['name', 'avatarUrl']) for f in followed_user_list]
    return jsonify({'data': data}), 200


@user_blueprint.route('/followers/list/', methods=['GET'])
@checkLogin
def followers_list():
    followers = g.user.followers.all()
    data = [serializer(f, ['name', 'avatarUrl']) for f in followers]
    return jsonify({'data': data}), 200


@user_blueprint.route('/report/<uid>/', methods=['GET'])
@checkLogin
def report(uid):
    user = User.query.get_or_404(uid)
    count = redis_service.incr('report-' + str(user.id))
    if count > 3:
        user.is_banned = True
        db.session.add(user)
        db.session.commit()
    return jsonify({'msg': 'OK'}), 200


@user_blueprint.route('/apply/', methods=['GET'])
@checkLogin
def apply():
    detail = request.json['detail']
    data = json.dumps({
        'user_id': g.user.id,
        'detail': detail,
        'apply_time': datetime.datetime.utcnow
    })
    redis_service.lpush('apply_list', data)
    return jsonify({'msg': 'OK'}), 200
