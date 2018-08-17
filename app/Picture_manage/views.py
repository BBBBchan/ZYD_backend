from flask import request,g, jsonify
from . import pictrue_manage_blueprint as picture_manage
from app.middlewares import checkLogin
from app.models import *


#增加作品类型，修改，删除仅可管理员后台操作
@picture_manage.route('/add_category', methods=['GET','POST'])
@checkLogin
def add_category():
    data = request.json
    user_id = data.get('user_id')
    # 对请求的权限进行控制
    request_user = User.query.filter_by(id=user_id).first()
    if request_user is None:
        return jsonify({'message':'must have user_id'}), 403
    if request_user == g.user and g.user.is_admin():
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
    else:
        return jsonify({'message':"only admin can"}),403


@picture_manage.route('/change_category', methods=['GET','POST'])
@checkLogin
def change_category():
    data = request.json
    user_id = data.get('user_id',g.user.id)
    request_user = User.query.filter_by(id=user_id).first()
    if request_user is None:
        return jsonify({'message': 'must have user_id'}), 403
    if request_user == g.user and g.user.is_admin():
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
    else:
        return jsonify({'message':"only admin can"}),403


@picture_manage.route('/delete_category/<category_id>')
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


# 增加作品标签，修改，删除仅课管理员后台操作
@picture_manage.route('/add_tag',methods=['GET','POST'])
@checkLogin
def add_tag():
    data = request.json
    if g.user.is_admin():
        tag_name = data.get('tag_name')
        if tag_name is None:
            return jsonify({'message':'no tag name'}), 403
        new_tag = Tag(name=tag_name)
        try:
            db.session.add(new_tag)
            db.session.commit()
        except:
            db.session.rollback()
    else:
        return jsonify({'message': "only admin can"}), 403
