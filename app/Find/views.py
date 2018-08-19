from flask import g,request,jsonify
from app.models import *
from . import find
from ..middlewares import checkLogin
import math
from .. import config


# 推荐页面
@find.route('/recommend/<int:page>')
def recommend(page):
    hot_pictures = HotOrder.query.all()
    pic_ids = []
    for pic in hot_pictures[10*(page-1):10*page]:
        pic_ids.append(pic.picture_id)
    pictures = Picture.query.filter(Picture.id.in_(pic_ids)).all()
    result = []
    for picture in pictures:
        re = {
            'id':picture.id,
            'name':picture.name,
            'url':picture.url,
            'author_id':picture.author_id,
            'author_name': picture.author.name
        }
        result.append(re)
    return jsonify(result)

# 类型feed页面,
@find.route('/category_recommend', methods=['POST'])
def type_recommend():
    data = request.json
    category_id = data.get('category_id')
    page = data.get('page',1)
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
    if len(temp) > 10*page:
        temp = temp[10*(page-1):10*page]
    elif len(temp) > 10 * (page-1):
        temp = temp[10*(page-1):]
    elif len(temp) < 10*(page-1):
        return jsonify({'no more picture'}), 404
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

@find.route('/square/<int:page>')
@checkLogin
def square(page):
    user = g.user
    user_followers = user.followed.all()
    request_time = datetime.now()
    request_picture = {}
    for user in user_followers:
        for pic in user.pictures.all():
            request_picture[pic.id] = (request_time - pic.upload_time).seconds
    temp = sorted(request_picture.items(),key=lambda e:e[1])
    pic_temp = dict(temp).keys()
    # 按时间计算的图片集
    square_picture = Picture.query.filter(Picture.id.in_(pic_temp)).all()
    HotOrder = Picture.query.all()
    try:
        square_picture = square_picture[7*(page-1):7*page] + HotOrder[3*(page-1):3*page]
    except:
        return jsonify({'message':'no more picture'}), 404
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