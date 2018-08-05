from flask import Blueprint, request, abort, jsonify
from flask.views import MethodView

from app.models import User, db, ApplyMessage, Role, PushMessage
from app.utils.serializers import serializer

admin_blueprint = Blueprint('admin_blueprint', __name__)


@admin_blueprint.route('/apply/list/', methods=['GET'])
def get_apply_list():
    try:
        apply_list = ApplyMessage.query.all().order_by(ApplyMessage.created_time.desc())
    except Exception as e:
        return jsonify({'error': e}), 500
    data = [serializer(instance, ['applicant_id', 'applicant', 'created_time', 'detail']) for instance in apply_list]
    return jsonify({'data': data}), 200


@admin_blueprint.route('/apply/<uid>/', methods=['GET'])
def apply_manage(uid):
    is_passed = request.json['is_passed']
    if is_passed:
        user = User.query.get_or_404(uid)
        try:
            if user.role.name == 'User':
                # 普通用户-->设计师
                user.role = Role.query.filter_by(permission=0x3fff).first()
            else:
                # 设计师-->特约设计师
                user.role = Role.query.filter_by(permission=0x1fff).first()
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': e}), 500
        if user.role.permission == 0x3fff:
            content = '申请通过, 您已成为设计师'
        else:
            content = '申请通过, 您已成为特约设计师'
        try:
            push_message = PushMessage(receiver_id=uid, content=content)
        except Exception as e:
            return jsonify({'error': e}), 500
    else:
        content = '很遗憾，申请未通过'
        try:
            push_message = PushMessage(receiver_id=uid, content=content)
        except Exception as e:
            return jsonify({'error': e}), 500

    db.session.add(push_message)
    db.session.commit()
    return jsonify({'msg': 'OK'}), 200


@admin_blueprint.route('/blacklist/', methods=['GET'])
def blacklist():
    users = User.query.filter_by(is_banned=True).all()
    return jsonify({'blacklist': users})


@admin_blueprint.route('/blacklist/<uid>/', methods=['GET'])
def blacklist_add_or_remove_user(uid):
    user = User.query.get_or_404(uid)
    try:
        user.is_banned = not user.is_banned
        db.session.add(user)
        db.session.commit()
    except:
        abort(500)
    return jsonify({'msg': 'OK'}), 200


class UserView(MethodView):
    def get(self):
        # 获取特定类型的用户列表
        try:
            permission = request.json['permission']
        except:
            abort(400)
        orders_url = '/order/list/'
        works_url = '/picture/list/'
        showcases_url = '/showcase/list/'
        extra_dict = {'orders': orders_url, 'works': works_url, 'showcases': showcases_url}
        query_set = User.query.filter_by(permission=permission).order_by(User.created_time.desc())
        data = [serializer(instance, ['id', 'name', 'created_time', 'last_login', 'tag', 'pricing'], extra_dict) for
                instance in query_set]
        return jsonify({'data': data}), 200

    def post(self, uid):
        # 将用户加入/移除黑名单
        user = User.query.get_or_404(uid)
        try:
            user.is_banned = not user.is_banned
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': e}), 500

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

        db.session.add(user)
        db.session.commit()
        # 向用户推送的取消/降级消息
        push_message = PushMessage(receiver=user, content=content)
        db.session.add(push_message)
        db.session.commit()
        return jsonify({'msg': 'OK'}), 200

    def delete(self, uid):
        # 删除用户
        user = User.query.get_or_404(uid)
        try:
            db.session.remove(user)
            db.session.commit()
        except Exception as e:
            return jsonify({'error': e}), 500


user_view = UserView.as_view('user')
admin_blueprint.add_url_rule('/user/', view_func=user_view, methods=['GET'])
admin_blueprint.add_url_rule('/user/<uid>/', view_func=user_view, methods=['POST', 'PUT', 'DELETE'])
