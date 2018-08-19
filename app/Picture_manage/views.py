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


# 增加作品标签，删除仅可管理员后台操作
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
            return jsonify({'message':'add successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'add failure'})
    else:
        return jsonify({'message': "only admin can"}), 403


@picture_manage.route('/delete_tag/<int:tag_id>')
@checkLogin
def delete_tag(tag_id):
    if g.user.is_admin():
        tag = Tag.query.filter_by(id=tag_id).first()
        if tag is None:
            return jsonify({'message':'no this tag'}), 404
        try:
            db.session.delete(tag)
            db.session.commit()
            return jsonify({'message':'delete successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'delete failure'})


# 图片申请上推荐，仅图片作者课申请
@picture_manage.route('/apply_recommend/<int:picture_id>')
@checkLogin
def want_recommend(picture_id):
    picture = Picture.query.filter_by(id=picture_id).first()
    if g.user != picture.author_id:
        return jsonify({'message':'only author can apply'}), 401
    if picture.isrecommend != 0:
        return jsonify({'message':'had applied'}), 401
    picture.isrecommend = 1
    try:
        db.session.add(picture)
        db.session.commit()
        return jsonify({'message':'apply successful'})
    except:
        db.session.rollback()
        return jsonify({'message':'apply failure'})


# 获取申请上推荐的图片列表仅管理员可看
@picture_manage.route('/apply_list')
@checkLogin
def apply_picture_list():
    if g.user.is_admin():
        apply_pictures = Picture.query.filter_by(isrecommend=1).all()
        if len(apply_pictures) > 0:
            result = []
            for picture in apply_pictures:
                re = {'picture_id':picture.id,
                      'picture_name':picture.name,
                      'picture_url':picture.url,
                      'picture_author':picture.author_id
                      }
                result.append(re)
            return jsonify(result)
        else:
            return jsonify({'message':'no picture'})
    else:
        return jsonify({'message':'no permission watch'}), 401


# 管理员是否同意图片上推荐
@picture_manage.route('/judgment_apply', methods=['POST','GET'])
@checkLogin
def judgment_apply():
    if g.user.is_admin():
        data = request.json
        apply_id = data.get('picture_id')
        if apply_id is None:
            return jsonify({'message':'data missing'}), 401
        apply_picture = Picture.query.filter_by(id=apply_id).first()
        if apply_picture is None or apply_picture.isrecommend != 1:
            return jsonify({'message':'no picture or not apply'}), 404
        judgment = data.get('judgment',False)
        if judgment:
            apply_picture.isrecommend = 2
        else:
            apply_picture.isrecommend = 0
        try:
            db.session.add(apply_picture)
            db.session.commit()
            return jsonify({'message':'successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'failure'})
    else:
        return jsonify({'only admin can'})


# 同意推荐的列表
@picture_manage.route('/recommend_list')
@checkLogin
def apply_picture_list():
    if g.user.is_admin():
        apply_pictures = Picture.query.filter_by(isrecommend=2).all()
        if len(apply_pictures) > 0:
            result = []
            for picture in apply_pictures:
                re = {'picture_id':picture.id,
                      'picture_name':picture.name,
                      'picture_url':picture.url,
                      'picture_author':picture.author_id
                      }
                result.append(re)
            return jsonify(result)
        else:
            return jsonify({'message':'no picture'})
    else:
        return jsonify({'message':'no permission watch'}), 401

@picture_manage.route('/cancel_recommend/<int:picture_id>')
@checkLogin
def cancel_recommend(picture_id):
    if g.user.is_admin():
        picture = Picture.query.filter_by(id=picture_id).first()
        if picture is None:
            return jsonify({'message':'no picture'})
        picture.isrecommend = 0
        try:
            db.session.add(picture)
            db.session.commit()
            return jsonify({'message':'cancel successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'cancel failure'})
    else:
        return jsonify({'message':'only admin can cancel'})



#  选择某图片上轮播图
@picture_manage.route('/choose_carousel/<int:picture_id>')
@checkLogin
def choose_carousel(picture_id):
    if g.user.is_admin():
        picture = Picture.query.filter_by(id=picture_id).first()
        if picture is None:
            return jsonify({'message':'no this picture'})
        picture.isrecommend = 3
        try:
            db.session.add(picture)
            db.session.commit()
            return jsonify({'message':'ok'})
        except:
            db.session.rollback()
            return jsonify({'message':'failure'})
    else:
        return jsonify({'message':'only admin can'})


#获得轮播图列表
@picture_manage.route('/carousel_list')
@checkLogin
def carousel_list():
    if g.user.is_admin():
        apply_pictures = Picture.query.filter_by(isrecommend=3).all()
        if len(apply_pictures) > 0:
            result = []
            for picture in apply_pictures:
                re = {'picture_id':picture.id,
                      'picture_name':picture.name,
                      'picture_url':picture.url,
                      'picture_author':picture.author_id
                      }
                result.append(re)
            return jsonify(result)
        else:
            return jsonify({'message':'no picture'})
    else:
        return jsonify({'message':'no permission watch'}), 401



# 管理员将某图片撤下轮播图
@picture_manage.route('/cancel_carousel/<int:picture_id>')
@checkLogin
def cancel_carousel(picture_id):
    if g.user.is_admin():
        picture = Picture.query.filter_by(id=picture_id).first()
        if picture is None:
            return jsonify({'message':'no picture'}), 404
        picture.isrecommend = 0
        try:
            db.session.add(picture)
            db.session.commit()
            return jsonify({'message':'cancel successful'})
        except:
            db.session.rollback()
            return jsonify({'message':'cancel failure'})
    else:
        return jsonify({'message':'only admin can cancel'}), 401