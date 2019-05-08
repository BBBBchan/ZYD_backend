import datetime

from flask import request, jsonify, abort, g, url_for, current_app

from app.middlewares import checkLogin
from app.models import User, ReportMessage, ApplyMessage
from app.user import user_blueprint
from app.utils.serializers import serializer, save_or_not
from app.utils.utils import upload_avatar_v1, db_handler
from app.utils.wx_api import get_session_key_and_openid, generate_3rd_session, update_token


@user_blueprint.route('/login/', methods=['POST'])
def login():
    data = request.json

    code = data.get('code')
    if code is None:
        abort(400)

    session_key, openid = get_session_key_and_openid(code)
    if session_key is None or openid is None:
        return abort(400)

    user = User.query.filter_by(openid=openid).first()

    if user is None:
        # user为空，说明为新用户，获取其信息录入数据库
        try:
            user = User(openid=openid)
        except Exception as e:
            current_app.logger.error(e)
            abort(500)
        db_handler(user)
        # 让用户成为他自己的粉丝
        db_handler(user.follow(user))

    user.last_login = datetime.datetime.utcnow()
    db_handler(user)

    token = generate_3rd_session(session_key, openid)

    return jsonify({'token': token, 'uid': user.id,
                    'detail_url': url_for('user_blueprint.get_user_info', uid=user.id, _external=True)}), 200


@user_blueprint.route('/token/', methods=['GET'])
def generate_new_token():
    """
    更新用户token
    """
    token = request.headers.get('Authorization')
    if token is None:
        abort(400)
    new_token = update_token(token)
    return jsonify({'token': new_token}), 200


@user_blueprint.route('/<uid>/', methods=['GET'])
@checkLogin
def get_user_info(uid):
    user = User.query.get_or_404(uid)

    if user.is_designer() or user.is_super_designer():
        data = serializer(user, ['id', 'name', 'avatarUrl', 'tag', 'last_login'])
    else:
        data = serializer(user, ['id', 'name', 'avatarUrl', 'last_login'])

    data.update({'role': str(user.role),
                 'followed': url_for('user_blueprint.followed_list', _external=True),
                 'followers': url_for('user_blueprint.followers_list', _external=True)})
    if g.user == user:
        data.update({'orders': url_for('order_blueprint.get_user_orders', _external=True)})

    return jsonify({'data': data}), 200


@user_blueprint.route('/', methods=['POST'])
@checkLogin
def change_user_info():
    data = request.json
    user = g.user
    if user.is_designer():
        save_or_not(user, ['name', 'tag'], data)
    else:
        save_or_not(user, ['name'], data)
    return jsonify({'message': '修改用户信息成功', 'uid': user.id}), 200


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
    保存头像至OSS
    """
    avatarUrl = request.json.get('avatarUrl')
    if avatarUrl is None:
        abort(400)
    g.user.avatarUrl = avatarUrl
    db_handler(g.user)

    return jsonify({'message': '操作成功'}), 200


@user_blueprint.route('/relationship/<uid>/', methods=['GET'])
@checkLogin
def follow_or_unfollow(uid):
    received_user = User.query.get_or_404(uid)
    if g.user.is_following(received_user):
        g.user.unfollow(received_user)
    else:
        g.user.follow(received_user)
    db_handler(g.user)
    return jsonify({'message': '操作成功'}), 200


@user_blueprint.route('/followed/list/', methods=['GET'])
@checkLogin
def followed_list():
    uid = request.args.get('uid')
    if uid:
        user = User.query.get_or_404(int(uid))
    else:
        # 默认查看当前登录用户的关注列表
        user = g.user
    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    followed_count = user.followed.count()
    pagination = user.followed.paginate(int(page_num), per_page=int(page_count), error_out=False)
    followed_user_list = pagination.items
    # data = [serializer(f, ['id', 'name', 'avatarUrl']) for f in followed_user_list]
    data_set = []
    for f in followed_user_list:
        data = {"id": f.id, "name": f.name, "avatarUrl": f.avatarUrl,
                "detail_url": url_for('user_blueprint.get_user_info', uid=f.id, _external=True)}
        data_set.append(data)
    return jsonify({'data': data_set, 'count': pagination.total,
                    'total_pages': pagination.pages, "followed_count": followed_count}), 200


@user_blueprint.route('/followers/list/', methods=['GET'])
@checkLogin
def followers_list():
    uid = request.args.get('uid')
    if uid:
        user = User.query.get_or_404(int(uid))
    else:
        # 默认查看当前登录用户的关注列表
        user = g.user
    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    follower_count = user.followers.count()
    pagination = user.followers.paginate(int(page_num), per_page=int(page_count), error_out=False)
    followers = pagination.items
    data_set = []
    for f in followers:
        data = {"id": f.id, "name": f.name, "avatarUrl": f.avatarUrl,
                "detail_url": url_for('user_blueprint.get_user_info', uid=f.id, _external=True),
                "is_followed": g.user.is_following(f)}
        data_set.append(data)
    return jsonify({'data': data_set, 'count': pagination.total,
                    'total_pages': pagination.pages, 'follower_count': follower_count}), 200


@user_blueprint.route('/report/<uid>/', methods=['POST'])
@checkLogin
def report(uid):
    reason = request.json.get('reason')
    if reason is None:
        abort(400)
    reported_user = User.query.get_or_404(uid)
    try:
        report_message = ReportMessage(reason=reason, reported=reported_user, reporter=g.user)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    db_handler(report_message)
    return jsonify({'message': '举报成功'}), 200


@user_blueprint.route('/apply/', methods=['POST'])
@checkLogin
def apply():
    detail = request.json.get('detail')
    if detail is None:
        abort(400)
    user = g.user
    if user.is_designer():
        apply_type = '特约设计师'
    elif not user.is_super_designer():
        apply_type = '设计师'
    else:
        return jsonify({'error': '您已经是特约设计师了，无需再进行申请'}), 404
    try:
        apply_message = ApplyMessage(applicant=user, detail=detail, apply_type=apply_type)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)
    db_handler(apply_message)
    return jsonify({'message': '操作成功'}), 200

