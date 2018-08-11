from flask import g,request,jsonify
from app.models import *
from . import find
from ..middlewares import checkLogin
import math
from .. import config

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

# 推荐页面
@find.route('/recommend')
@checkLogin
def recommend():
    all_picture = Picture.query.all()
    pictures = {}
    request_time = datetime.now()
    for picture in all_picture:
        # 计算热度
        score = math.log((0.3*picture.clicks+0.2*picture.stars.count()
                      + 0.3*picture.comments.count() + 0.2*picture.share_count)/4)+(
                request_time-config.base_time).seconds/36000
        pictures[picture.id] = score
    # 根据热度排序
    temp_result = sorted(pictures.items(),key=lambda e:e[1], reverse=True)
    temp = dict(temp_result).keys()
    if len(temp) > 20:
        temp = temp[:20]
    hot = Picture.query.filter(Picture.id.in_(temp)).all()
    special_picture = Picture.query.filter_by(iscommend=True).all()
    # 返回编辑推荐和热度前20
    re = special_picture + hot
    result = []
    for r in re:
        temp_r = {'id':r.id,
                  'picture_name':r.name,
                  'url': r.url,
                  'author_id': r.author_id,
                  'author_name': r.author.name
                  }
        result.append(temp_r)

    return jsonify(result)

# 类型feed页面,
@find.route('/category_recommend/<category_id>')
@checkLogin
def type_recommend(category_id):
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return jsonify({'message':'no this category'})
    request_time = datetime.now()
    c_pictures = category.pictures.all()
    hot_cate = {}
    for picture in c_pictures:
        score = math.log((0.3*picture.clicks+0.2*picture.stars.count()
                      + 0.3*picture.comments.count() + 0.2*picture.share_count)/4)+(
                request_time-config.base_time).seconds/36000
        hot_cate[picture.id] = score
    temp_result = sorted(hot_cate.items(), key=lambda e: e[1], reverse=True)
    temp = dict(temp_result).keys()
    if len(temp) >20:
        temp = temp[:20]
    hot = Picture.query.filter(Picture.id.in_(temp)).all()
    special_picture = Picture.query.filter_by(iscommend=True,category_id=category_id).all()
    # 返回编辑推荐和热度前20
    re = special_picture + hot
    result = []
    for r in re:
        temp_r = {'id': r.id,
                  'picture_name': r.name,
                  'url': r.url,
                  'author_id': r.author_id,
                  'author_name': r.author.name
                  }
        result.append(temp_r)

    return jsonify(result)

@find.route('/square')
@checkLogin
def square():
    user = g.user
    user_followers = user.followed.all()
    request_time = datetime.now()
    request_picture = {}
    for user in user_followers:
        for pic in user.pictures.all():
            request_picture[pic.id] = (request_time - pic.upload_time).seconds
    temp = sorted(request_picture.items(),key=lambda e:e[1])
    pic_temp = dict(temp).keys()
    if len(pic_temp) >=20:
        pic_temp = pic_temp[:20]
    square_picture = Picture.query.filter(Picture.id.in_(pic_temp)).all()
    result = []
    for picture in square_picture:
        re = {'id': picture.id,
              'name': picture.name,
              'url': picture.url,
              'author_id': picture.author_id,
              'author_name': picture.author.name,
              'time': picture.upload_time
              }
        result.append(re)
    return jsonify(result)
