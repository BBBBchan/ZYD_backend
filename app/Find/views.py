from flask import g,request,jsonify
from app.models import *
from . import find
from ..middlewares import checkLogin

@find.route('/add_category')
@checkLogin
def add_category():
    data = request.json
    user_id = data.get('user_id',g.user.id)
    category_name = data.get('category_name')
    description = data.get('description','这个人懒死了什么人也没写')
    if category_name is None:
        return jsonify({'message': 'no name'}), 401
    new_category_name = Category(name=category_name, description=description)
    try:
        db.session.add(new_category_name)
        db.session.commit()
        return jsonify({'message':'successful'})
    except:
        db.session.rollback()
        return jsonify({'message':'failure'}), 401

