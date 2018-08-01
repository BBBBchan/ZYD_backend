from flask import Blueprint, request, abort, jsonify

from app.models import User, db

admin_blueprint = Blueprint('admin_blueprint', __name__)


@admin_blueprint.route('/apply/<uid>/', methods=['GET'])
def apply_manage(uid):
    is_passed = request.json['is_passed']
    if is_passed:
        user = User.query.get_or_404(uid)
        try:
            user.role_id = 2
            db.session.add(user)
            db.session.commit()
        except:
            abort(500)
        # success msg
    else:
        pass
        # fail msg
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





