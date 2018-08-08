from flask import g,request,jsonify
from app.models import *
from . import find
from ..middlewares import checkLogin

@find.route('/add_category', methods=['GET','POST'])
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


@find.route('/change_category', methods=['GET','POST'])
@checkLogin
def change_category():
    data = request.json
    user_id = data.get('user_id',g.user.id)
    category_id = data.get('category_id')
    if category_id is None:
        return jsonify({'message':'data missing'}), 401
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return jsonify({'message': 'no this category'}), 404
    new_name = data.get('new_name',category.name)
    new_description = data.get('new_description',category.description)
    category.name = new_name
    category.description = new_description
    try:
        db.session.add(category)
        db.session.commit()
        return jsonify({'message':'change successful'}), 200
    except:
        db.session.rollback()
        return jsonify({'message': 'change failure'}), 401

@find.route('/delete_category/<category_id>')


@find.route('/delete_category/<category_id>')
@checkLogin
def delete_category(category_id):
    if g.user.is_admin():
        category = Category.query.filter_by(id=category_id).first()
        null_category = Category.query.filter_by(id=1).first()
        all_pictures = Picture.query.filter_by(category=category).all()
        try:
            for picture in all_pictures:
                picture.category_id = null_category.id
                db.session.add(picture)
                db.session.commit()
        except:
            return jsonify({'message': 'delete successful'})
        if category is None:
            return jsonify({'message':'had delete'}), 404
        try:
            db.session.delete(category)
            db.session.commit()
            return jsonify({'message':'delete successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'delete failure'})
    else:
        return jsonify({'message': 'no permission'})