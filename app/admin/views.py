from flask import Blueprint, request, abort, jsonify
from flask.views import MethodView

from app.config import logger
from app.models import User, db, ApplyMessage, Role, PushMessage
from app.utils.serializers import serializer
from app.utils.utils import db_handler

admin_blueprint = Blueprint('admin_blueprint', __name__)


@admin_blueprint.route('/apply/list/', methods=['GET'])
def get_apply_list():
    try:
        apply_list = ApplyMessage.query.all().order_by(ApplyMessage.created_time.desc())
    except Exception as e:
        logger.error(e)
        return jsonify({'message': '获取申请列表失败'}), 500
    data = [serializer(instance, ['applicant_id', 'applicant', 'created_time', 'detail']) for instance in apply_list]
    return jsonify({'data': data}), 200


@admin_blueprint.route('/apply/<uid>/', methods=['GET'])
def apply_manage(uid):
    is_passed = request.json['is_passed']
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
        try:
            push_message = PushMessage(receiver_id=uid, content=content)
        except Exception as e:
            logger.error(e)
            abort(500)
    else:
        content = '很遗憾，申请未通过'
        try:
            push_message = PushMessage(receiver_id=uid, content=content)
        except Exception as e:
            logger.error(e)
            abort(500)

    db_handler(push_message)
    return jsonify({'message': '操作成功'}), 200


@admin_blueprint.route('/blacklist/', methods=['GET'])
def blacklist():
    users = User.query.filter_by(is_banned=True).all()
    return jsonify({'blacklist': users})


@admin_blueprint.route('/blacklist/<uid>/', methods=['GET'])
def blacklist_add_or_remove_user(uid):
    user = User.query.get_or_404(uid)
    user.is_banned = not user.is_banned
    db_handler(user)
    return jsonify({'message': '操作成功'}), 200


class UserView(MethodView):
    def get(self):
        # 获取特定类型的用户列表
        try:
            permission = request.json['permission']
        except Exception as e:
            logger.error(e)
            abort(400)

        query_set = User.query.filter_by(permission=permission).order_by(User.created_time.desc())
        data_set = []
        for user in query_set:
            data = serializer(user, ['id', 'name', 'last_login', 'created_time'])
            data.update({'role': str(user.role),
                         'pictures': '/user/{uid}/picture/list/'.format(uid=user.id),
                         'showcases': '/user/{uid}/showcase/list/'.format(uid=user.id),
                         'orders': '/user/{uid}/order/list/'.format(uid=user.id)})
            data_set.append(data)
        return jsonify({'data': data_set}), 200

    def post(self, uid):
        # 将用户加入/移除黑名单
        user = User.query.get_or_404(uid)
        user.is_banned = not user.is_banned
        db_handler(user)

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
        try:
            # 向用户推送的取消/降级消息
            push_message = PushMessage(receiver=user, content=content)
        except Exception as e:
            logger.error(e)
            abort(500)
        db_handler(push_message)
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
admin_blueprint.add_url_rule('/user/', view_func=user_view, methods=['GET'])
admin_blueprint.add_url_rule('/user/<uid>/', view_func=user_view, methods=['POST', 'PUT', 'DELETE'])
