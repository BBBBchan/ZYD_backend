from functools import wraps
from flask import request, abort, g

from app.config import logger
from app.utils.wx_api import get_token_value
from app.models import User, BackendUser


def checkLogin(f):
    """
    装饰器，用来进行用户认证
    若认证成功，则将当前用户附加在全局变量g.user上
    若认证失败，则返回状态码403
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_backend_user():
            # 若不是后台用户，则为小程序用户
            try:
                token = request.headers['Authorization']
                session_key, openid = get_token_value(token)
                user = User.query.filter_by(openid=openid).first()
            except:
                abort(403)
            g.user = user
        return f(*args, **kwargs)
    return decorated_function


def checkAdmin(f):
    """
    装饰器，用来进行管理员认证
    若认证成功，则将当前用户附加在全局变量g.user上
    若认证失败，则返回状态码403
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        check_backend_user()
        return f(*args, **kwargs)
    return decorated_function


def check_backend_user():
    """
    后台用户认证
    """
    username = request.headers.get('username')
    if username:
        password = request.headers.get('password')
        if password is None:
            abort(403)
        user = BackendUser.query.filter_by(username=username).first()
        if user is None:
            abort(404)
        if user.check_password(password):
            g.user = user
            return True
    return False
