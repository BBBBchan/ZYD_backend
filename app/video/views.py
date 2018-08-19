from flask import request, jsonify
from sqlalchemy import extract

from app.middlewares import checkLogin
from . import video_blueprint
from ..models import *


@video_blueprint.route('/')
def index():
    return 'hello world'


@video_blueprint.route('/nologin')
def no_login():
    return 'no login', 401


@checkLogin
@video_blueprint.route('/video_list', methods=['POST'])
def video_list():
    request_data = request.json
    print(request_data)
    page_count = request_data.get('pagecount', 10)
    page = request_data.get('page', 1)
    type = request_data.get('query_type')
    if type == None:
        return jsonify({'message': 'no type'}), 400
    if type == 'user_id':
        author_id = request_data.get('query_key')
        re = Video.query.filter_by(author_id=author_id).all()
        result = []
        for i in range(page_count * page - 1, page_count * page):
            try:
                video_info = {
                    'video_id': re[i].id,
                    'video_name': re[i].name,
                    'video_url': re[i].url,
                    'video_type': re[i].category.name,
                    'video_author': re[i].author.name,
                    'video_star_count': StarVideo.query.filter_by(content_id=re[i].id).count(),
                    'video_comment_count': CommentVideo.query.filter_by(content_id=re[i].id).count(),
                    'video_click': re[i].clicks
                }
                result.append(video_info)
            except:
                break
        return jsonify(result)
    if type == 'type':
        query_key = request_data.get('query_key')
        category = Category.query.filter_by(name=query_key).first()
        if category is None:
            return jsonify({'message': 'no category'}), 404
        re = Video.query.filter_by(category_id=category.id).all()
        result = []
        for i in range(page_count * page - 1, page_count * page):
            try:
                video_info = {
                    'video_id': re[i].id,
                    'video_name': re[i].name,
                    'video_url': re[i].url,
                    'video_type': re[i].category.name,
                    'video_author': re[i].author.name,
                    'video_star_count': StarVideo.query.filter_by(content_id=re[i].id).count(),
                    'video_comment_count': CommentVideo.query.filter_by(content_id=re[i].id).count(),
                    'video_click': re[i].clicks
                }
                result.append(video_info)
            except:
                break
        return jsonify(result)
    # 按时间查询需要和PM对一下需求可能有变动先待定
    query_re = None
    if type == 'year':
        query_key = request_data.get('query_key')
        query_re = Video.query.filter(extract("year", Video.upload_time) == query_key).all()
    elif type == 'month':
        query_key = request_data.get('query_key')
        query_re = Video.query.filter(extract("month", Video.upload_time) == query_key).all()
    elif type == 'day':
        query_key = request_data.get('query_key')
        query_re = Video.query.filter(extract('day', Video.upload_time) == query_key).all()
    elif type == 'TimeRange':
        startime = request_data.get('query_key').get('starday')
        endtime = request_data.get('query_key').get('endday')
        if startime is not None and endtime is not None:
            star = datetime.strftime(startime, "%Y-%m-%d")
            end = datetime.strftime(endtime, '%Y-%m-%d')
            query_re = Video.query.filter(Video.upload_time.betwwen(star, end)).all()
    if len(query_re) > 0:
        result = []
        for i in range(page_count * page - 1, page_count * page):
            try:
                video_info = {
                    'video_id': query_re[i].id,
                    'video_name': query_re[i].name,
                    'video_url': query_re[i].url,
                    'video_type': query_re[i].category.name,
                    'video_author': query_re[i].author.name,
                    'video_star_count': StarVideo.query.filter_by(
                        content_id=query_re[i].id).count(),
                    'video_comment_count': CommentVideo.query.filter_by(
                        content_id=query_re[i].id).count(),
                    'video_click': query_re[i].clicks
                }
                result.append(video_info)
            except:
                break
        return jsonify(result)


@checkLogin
@video_blueprint.route('/upload_video', methods=['POST'])
def upload_video():
    upload_data = request.json
    user_id = upload_data.get('user_id')
    video_name = upload_data.get('video_name')
    video_url = upload_data.get('video_url')
    video_type = upload_data.get('type')
    if user_id is None or video_name is None \
            or video_url is None or video_type is None:
        return jsonify({'message': 'argument missing'}), 403
    category = Category.query.filter_by(name=video_type).first()
    author = User.query.filter_by(id=user_id).first()
    if category is None and author is None:
        return 404
    new_Video = Video(name=video_name, url=video_url,
                      category_id=category.id, category=category,
                      author_id=user_id, author=author)
    db.session.add(new_Video)
    try:
        db.session.commit()
        return jsonify({'message': 'upload successful'}), 200
    except:
        db.session.rollback()
        return jsonify({'message': 'failure'}), 403
