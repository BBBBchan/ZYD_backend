from functools import wraps
from flask import request, abort, g
from app.utils.wx_api import get_token_value
from app.models import User


def checkLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = request.headers['Authorization']
            session_key, openid = get_token_value(token)
            user = User.query.filter_by(openid=openid).first()
        except:
            abort(403)
        g.user = user
        return f(*args, **kwargs)
    return decorated_function
