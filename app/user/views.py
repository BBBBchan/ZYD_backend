from flask import request, jsonify, abort, g

from app.middlewares import checkLogin
from app.models import User, db, ReportMessage, ApplyMessage
from app.user import user_blueprint
from app.utils.serializers import serializer, save_or_not
from app.utils.utils import upload_avatar_v1, db_handler
from app.utils.wx_api import get_session_key_and_openid, generate_3rd_session, update_token
from app.config import logger


@user_blueprint.route('/login/', methods=['POST'])
def login():
    data = request.json

    code = data.get('code')
    if code is None:
        abort(400)

    session_key, openid = get_session_key_and_openid(code)
    if session_key is None or openid is None:
        return abort(400)

    try:
        user = User.query.filter_by(openid=openid).first()
    except:
        user = None

    if user is None:
        # user为空，说明为新用户，获取其信息录入数据库
        try:
            user = User(openid=openid)
        except Exception as e:
            logger.error(e)
            abort(500)
        db_handler(user)
        # 让用户成为他自己的粉丝
        db_handler(user.follow(user))

    token = generate_3rd_session(session_key, openid)

    return jsonify({'token': token, 'uid': user.id}), 200


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
                 'followed': '/user/followed/list/',
                 'followers': '/user/followers/list/'})

    if g.user == user:
        data.update({'orders': '/order/list/'})

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
    page = request.json.get('page')
    if page is None:
        abort(400)
    followed_count = g.user.followed.count()
    pagination = g.user.followed.paginate(page, per_page=10, error_out=False)
    followed_user_list = pagination.items
    # data = [serializer(f, ['id', 'name', 'avatarUrl']) for f in followed_user_list]
    data_set = []
    for f in followed_user_list:
        data = {"id": f.id, "name": f.name, "avatarUrl": f.avatarUrl, "detail_url": '/user/{}'.format(f.id)}
        data_set.append(data)
    return jsonify({'data': data_set, 'count': pagination.total,
                    'total_pages': pagination.pages, "followed_count": followed_count}), 200


@user_blueprint.route('/followers/list/', methods=['GET'])
@checkLogin
def followers_list():
    page = request.json.get('page')
    if page is None:
        abort(400)
    follower_count = g.user.followers.count()
    pagination = g.user.followers.paginate(page, per_page=10, error_out=False)
    followers = pagination.items
    # data = [serializer(f, ['id', 'name', 'avatarUrl']) for f in followers]
    data_set = []
    for f in followers:
        data = {"id": f.id, "name": f.name, "avatarUrl": f.avatarUrl,
                "detail_url": '/user/{}'.format(f.id), "is_followed": g.user.is_following(f)}
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
        logger.error(e)
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
        logger.error(e)
        abort(500)
    db_handler(apply_message)
    return jsonify({'message': '操作成功'}), 200
