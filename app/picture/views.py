from . import picture_blueprint as picture
from flask import current_app,  request, jsonify, g
from app.middlewares import checkLogin
from app.models import *
from app.config import *

#  获取图片列表
@picture.route('/picture_list', methods=['POST', 'GET'])
def picture_list():
    data = request.json
    user_id = data.get('user_id')
    page = data.get('page', 1)
    page_count = data.get('page_count', 5)
    if user_id is None:
        return jsonify({'message': 'data missing'}), 401
    all_picture = Picture.query.filter_by(author_id=user_id).all()
    if len(all_picture) == 0:
        return jsonify({'message': 'no picture'}), 404
    result = []
    for i in range(page_count * page-1, page_count * page):
        re = {
            'picture_id': all_picture[i].id,
            'picture_name': all_picture[i].name,
            'picture_url': all_picture[i].url,
            'author_id': all_picture[i].author_id,
            'author_name': all_picture[i].author.name,
            'tag_name': all_picture[i].tag.name
        }
        result.append(re)
    return jsonify(result)

# 获取图片详情
@picture.route('/picture_detail/<int:picture_id>')
@checkLogin
def picture_detail(picture_id):
    picture = Picture.query.filter_by(id=picture_id).first()
    if picture is None:
        return jsonify({'message': 'no picture'}), 404
    result = {'picture_id': picture.id,
              'picture_name': picture.name,
              'author_id': picture.author_id,
              "author_name": picture.author.name,
              'upload_time': picture.upload_time,
              'share_count' : picture.share_count,
              'category_id': picture.category_id,
              'category_name': picture.category.name,
              'tag_id': picture.tag_id,
              'tag_name': picture.tag.name
              }
    user = g.user
    if StarPicture.query.filter_by(
            user_id=user.id,content_id=picture_id).first() is None:
        result['had_star'] = False
    else:
        result['had_star'] = True
    result['star_count'] = StarPicture.query.filter_by(content_id=picture_id).count()
    result['comment_count'] = CommentPicture.query.filter_by(content_id=picture_id).count()
    picture.clicks = picture.clicks + 1
    db.session.add(picture)
    db.session.commit()
    return jsonify(result)


# 上传图片
@picture.route('/upload_picture',methods=['POST','GET'])
@checkLogin
def upload_picture():
    data = request.json
    user_id = data.get('user_id',g.user.id)
    picture_name = data.get('picture_name')
    if picture_name is None:
        return jsonify({'message':'must have name'}), 401
    if Picture.query.filter_by(name=picture_name).first() is not None:
        return jsonify({'message': 'name had be used'}), 401
    picture_expend = data.get('picture_expend')
    if picture_expend is None:
        return jsonify({'message': 'data missing'}), 401
    picture_url = data.get('picture_url',None)
    picture_type = data.get('picture_type_id')
    picture_tag = data.get('picture_tag_id')
    if picture_type is None:
        return jsonify({'message':'no type'}), 401
    type = Category.query.filter_by(id=picture_type).first()
    tag = Tag.query.filter_by(id=picture_tag).first()
    if type is None or tag is None:
        return jsonify({'message': 'can not find this type'}), 404
    if picture_url is None:
        picture_url = 'https://'+ OSS_OPEN_IP + picture_name + picture_expend
    user = User.query.filter_by(id=user_id).first()
    newPic = Picture(name=picture_name,url=picture_url,
                     category=type,author=user,tag= tag)
    try:
        db.session.add(newPic)
        db.session.commit()
        return jsonify({'message':'upload successful'})
    except:
        db.session.rollback()
        return jsonify({'message':'upload failure'}),400


# 删除图片
@picture.route('/delete_picture/<int:picture_id>')
@checkLogin
def delete_picture(picture_id):
    picture = Picture.query.filter_by(id=picture_id).first()
    all_stars = StarPicture.query.filter_by(content_id=picture_id).all()
    all_comments = CommentPicture.query.filter_by(content_id=picture_id).all()
    try:
        for star_picture in all_stars:
            db.session.delete(star_picture)
            db.session.commit()
        for comment_picture in all_comments:
            db.session.delete(comment_picture)
            db.session.commit()
    except:
        db.session.rollback()
        return jsonify({'message':'delete failure'}),401
    try:
        db.session.delete(picture)
        db.session.commit()
        return jsonify({'message':'delete successful'})
    except:
        db.session.rollback()
        return jsonify({'message': 'delete failure'}), 401


#图片点赞/取消点赞
@picture.route('/star/<int:picture_id>')
@checkLogin
def star(picture_id):
    had_star= StarPicture.query.filter_by(
            content_id=picture_id).first()
    # 取消点赞
    if had_star is not None:
        db.session.delete(had_star)
        try:
            db.session.commit()
            return jsonify({'message':'unstar successful'})
        except:
            db.session.rollback()
            return jsonify({'unstar failure'}), 400
    else:
        # 点赞图片
        newStar = StarPicture(user_id = g.user.id,user=g.user,
                              content_id=picture_id,
                              content=Picture.query.filter_by(id=picture_id).first())
        try:
            db.session.add(newStar)
            db.session.commit()
            return jsonify({'message': 'star successful'})
        except:
            db.session.rollback()
            return jsonify({'message': 'star failure'}), 400


# 修改图片信息
@picture.route('/change_info', methods=['GET','POST'])
@checkLogin
def change_info():
    data = request.json
    user_id = data.get('user_id', g.user.id)
    picture_id = data.get('picture_id')
    try:
        picture = Picture.query.filter_by(id=picture_id,author_id=user_id).first()
        if picture is None:
            return jsonify({'message': 'no picture'}), 404
        else:
            picture_name = data.get('picture_name',picture.name)
            picture_type = data.get('picture_type_id')
            picture_tag = data.get('picture_tag_id')
            if picture_type is not None:
                new_type = Category.query.filter_by(id=picture_type).first()
                if new_type is None:
                    return jsonify({'message': 'no type'}), 404
                picture.category = new_type
            if picture_tag is not None:
                new_tag = Tag.query.filter_by(id=picture_tag).first()
                if new_tag is None:
                    return jsonify({'message': 'no tag'}), 404
                picture.tag = new_tag
            picture.name=picture_name
            db.session.add(picture)
            db.session.commit()
    except:
        db.session.rollback()
        return jsonify({'message':'data miss'}), 401

# 记录分享数
@picture.route('/share/<int:picture_id>')
@checkLogin
def share(picture_id):
    picture = Picture.query.filter_by(id=picture_id)
    if picture is None:
        return jsonify({'message':'no picture'}), 404
    picture.share_count = picture.share_count + 1
    db.session.add(picture)
    db.session.commit()
    return jsonify({'message': 'share successful'}),200


# 获得类型列表
@picture.route('/category_list')
def category_list():
    all_categorys = Category.query.all()
    result = [{'id': category.id,'name':category.name,'description': category.description}
              for category in all_categorys]
    return jsonify(result)

# 获得标签列表
@picture.route('/tag_list')
def tag_list():
    all_tags = Tag.query.all()
    result = [{'id':tag.id,'name':tag.name}
              for tag in all_tags]
    return jsonify(result)