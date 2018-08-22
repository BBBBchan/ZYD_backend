from flask import request, abort, jsonify
from flask.views import MethodView

from app.admin import admin_blueprint
from app.config import logger
from app.middlewares import checkAdmin
from app.models import User, db, ApplyMessage, Role, ReportMessage, BackendUser
from app.utils.serializers import serializer
from app.utils.utils import db_handler, message_confirm, push_message_to_user


@admin_blueprint.route('/login/', method=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username is None or password is None:
        abort(400)
    user = BackendUser.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    if user.check_password(password):
        user.login()
    else:
        abort(403)
    return jsonify({'message': '登陆成功'}), 200


@admin_blueprint.route('/apply/list/', methods=['GET'])
@checkAdmin
def get_apply_list():
    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    if page_num is None or page_count is None:
        abort(400)
    try:
        pagination = ApplyMessage.query.filter_by(status=False).order_by(ApplyMessage.created_time.desc())\
            .paginate(int(page_num), per_page=int(page_count), error_out=False)
        apply_list = pagination.items
    except Exception as e:
        logger.error(e)
        return jsonify({'message': '获取申请列表失败'}), 500
    data = [serializer(instance, ['id', 'applicant_id', 'applicant', 'created_time', 'detail'])
            for instance in apply_list]
    return jsonify({'data': data, 'count': pagination.total, 'total_pages': pagination.pages}), 200


@admin_blueprint.route('/apply/<uid>/', methods=['POST'])
@checkAdmin
def apply_manage(uid):
    is_passed = request.json.get('is_passed')
    if is_passed:
        user = User.query.get_or_404(uid)
        if user.role.permission == 0x03ff:
            # 普通用户-->设计师
            user.role = Role.query.filter_by(permission=0x3fff).first()
        else:
            # 设计师-->特约设计师
            user.role = Role.query.filter_by(permission=0x1fff).first()
        db_handler(user)
        if user.role.permission == 0x3fff:
            content = '申请通过, 您已成为设计师'
        else:
            content = '申请通过, 您已成为特约设计师'
        # 推送消息
        push_message_to_user(uid, content)
    elif is_passed is None:
        abort(400)
    else:
        content = '很遗憾，申请未通过'
        push_message_to_user(uid, content)
    message_confirm(ApplyMessage)
    return jsonify({'message': '操作成功'}), 200


@admin_blueprint.route('/report/list/', methods=['GET'])
@checkAdmin
def get_report_list():
    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    if page_num is None or page_count is None:
        abort(400)
    try:
        pagination = ReportMessage.query.filter_by(status=False).order_by(ReportMessage.created_time.desc())\
            .paginate(int(page_num), per_page=int(page_count), error_out=False)
        apply_list = pagination.items
    except Exception as e:
        logger.error(e)
        return jsonify({'message': '获取举报列表失败'}), 500
    data = [serializer(instance, ['id', 'reporter_id', 'reporter', 'reported', 'reported_id', 'reason', 'created_time'])
            for instance in apply_list]
    return jsonify({'data': data, 'count': pagination.total, 'total_pages': pagination.pages}), 200


@admin_blueprint.route('/report/<uid>/', methods=['POST'])
@checkAdmin
def report_manage(uid):
    is_banned = request.json.get('is_banned')
    if is_banned:
        user = User.query.get_or_404(uid)
        user.is_banned = True
        db_handler(user)
    elif is_banned is None:
        abort(400)
    return jsonify({'message': '操作成功'}), 200


@admin_blueprint.route('/blacklist/', methods=['GET'])
@checkAdmin
def blacklist():
    page_num = request.args.get('page_num', '1')
    page_count = request.args.get('page_count', '10')
    if page_num is None or page_count is None:
        abort(400)
    pagination = User.query.filter_by(is_banned=True).paginate(int(page_num), per_page=int(page_count), error_out=False)
    users = pagination.items
    data = [serializer(u, ['id', 'name']) for u in users]
    return jsonify({'data': data, 'count': pagination.total, 'total_pages': pagination.pages})


@admin_blueprint.route('/blacklist/<uid>/', methods=['GET'])
@checkAdmin
def blacklist_add_or_remove_user(uid):
    user = User.query.get_or_404(uid)
    user.is_banned = not user.is_banned
    db_handler(user)
    return jsonify({'message': '操作成功'}), 200


class UserView(MethodView):
    decorators = [checkAdmin]

    def get(self):
        # 获取特定类型的用户列表
        role_name = request.args.get('role')
        role = Role.query.filter_by(name=role_name).first()
        page_num = request.args.get('page_num', '1')
        page_count = request.args.get('page_count', '10')
        if role is None or page_num is None or page_count is None:
            abort(400)

        pagination = User.query.filter_by(role=role)\
            .order_by(User.created_time.desc()).paginate(int(page_num), per_page=int(page_count), error_out=False)
        query_set = pagination.items
        data_set = []
        for user in query_set:
            data = serializer(user, ['id', 'name', 'last_login', 'created_time'])
            data.update({'role': str(user.role)})
            data_set.append(data)
        return jsonify({'data': data_set, 'count': pagination.total, 'total_pages': pagination.pages}), 200

    def post(self, uid):
        # 将用户加入/移除黑名单
        user = User.query.get_or_404(uid)
        user.is_banned = not user.is_banned
        db_handler(user)
        return jsonify({'message': '操作成功'}), 200

    def put(self, uid):
        # 取消/降级用户设计师资格
        user = User.query.get_or_404(uid)
        if user.is_designer():
            # 设计师-->普通用户
            user.role = Role.query.filter_by(permission=0x03ff).first()
            content = '根据系统判决，您的身份降为普通用户'
        elif user.is_super_designer():
            # 特约设计师-->设计师
            user.role = Role.query.filter_by(permission=0x3fff).first()
            content = '根据系统判决，您的身份降为设计师'
        else:
            return abort(404)

        db_handler(user)
        # 向用户推送的取消/降级消息
        push_message_to_user(user.id, content)
        return jsonify({'msg': 'OK'}), 200

    def delete(self, uid):
        # 删除用户
        user = User.query.get_or_404(uid)
        try:
            db.session.remove(user)
            db.session.commit()
        except Exception as e:
            logger.error(e)
            abort(500)


user_view = UserView.as_view('user')
admin_blueprint.add_url_rule('/users/', view_func=user_view, methods=['GET'])
admin_blueprint.add_url_rule('/user/<uid>/', view_func=user_view, methods=['POST', 'PUT', 'DELETE'])
