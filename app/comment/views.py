from . import comment_blueprint
import json
from flask import current_app,  request, jsonify, g
from app.middlewares import checkLogin
from app.models import User, CommentPicture, datetime, db, Permission, Picture
from app.config import *

#获取评论列表
@comment_blueprint.route('/comment_list', methods=['POST'])
@checkLogin
def comment_list():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	pic_id = data.get('pic_id')
	if pic_id == None:
		return jsonify({'message':'获取图片id失败'}),401
	page_count = data.get('page_count', 10)
	page_num = data.get('page_num', 1)
	try:
		comment_all = CommentPicture.query.filter_by(content_id = pic_id).all()
	except:
		db.session.rollback()
		return jsonify({'message':'获取评论失败'}),402
	res = {}
	for i in range(page_count*(page_num-1),page_count*page_num):
		comment = {
			'comment_id':comment_all[i].id,
			'username': comment_all[i].commentator.name,
			'user_avatarurl': comment_all[i].commentator.avatarUrl,
			'comment_detail': comment_all[i].context,
			'comment_time': comment_all[i].created_time,
		}
		res.append(comment)
	return jsonify(res)

#修改评论
@comment_blueprint.route('/comment_modify', methods=['POST'])
@checkLogin
def comment_modify():
	data = request.json
	comment_id = data.get('comment_id')
	if comment_id == None:
		return jsonify({'message':'获取评论id失败'}),400
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),401
	pic_id = data.get('pic_id')
	if pic_id == None:
		return jsonify({'message':'获取图片id失败'}),402
	comment_detail = data.get('comment_detail')
	if comment_detail == None:
		return jsonify({'message':'获取评论内容失败'}),403

	try:	
		comment = CommentPicture.query.filter_by(id=comment_id,content_id=pic_id,commentator_id=user_id).first()
		if comment.context == comment_detail:
			return jsonify({'message':'评论内容未修改'}),405
		else:
			comment.context = comment_detail
			try:
				db.session.commit()
				return jsonify({'message':'修改评论成功'})
			except:
				db.session.rollback()
				return jsonify({'message':'修改评论失败'}),406
	except:
		db.session.rollback()
		return jsonify({'message':'获取评论失败'}),404

#删除评论
@comment_blueprint.route('/comment_delete', methods=['POST'])
@checkLogin
def comment_delete():
	data = request.json
	comment_id = data.get('comment_id')
	if comment_id == None:
		return jsonify({'message':'获取评论id失败'}),400
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),401
	pic_id = data.get('pic_id')
	if pic_id == None:
		return jsonify({'message':'获取图片id失败'}),402

	try:	
		comment = CommentPicture.query.filter_by(id=comment_id, content_id=pic_id, commentator_id=user_id).first()
		try:
			db.session.delete(comment)
			db.session.commit()
			return jsonify({'message':'删除成功'})
		except:
			db.session.rollback()
			return jsonify({'message':'删除失败'}),404
	except:
		db.session.rollback()
		return jsonify({'message':'获取评论失败'}),403

#添加评论
@comment_blueprint.route('/comment_upload', methods=['POST'])							
@checkLogin
def comment_upload():
	data = request.json
	user_id = data.get('user_id')
	
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	pic_id = data.get('pic_id')
	if pic_id == None:
		return jsonify({'message':'获取图片id失败'}),401
	comment_detail = data.get('comment_detail')
	if comment_detail == None:
		return jsonify({'message':'获取评论内容失败'}),402	
	comment_time = str(datetime.now())
	
	try:
		user = User.query.filter_by(id=user_id).first()
	except:
		db.session.rollback()
		return jsonify({'message':'用户不存在'}),403
	try:
		picture =Picture.query.filter_by(id=pic_id).first()
	except:
		db.session.rollback()
		return jsonify({'message':'未找到相应图片'}),404

	new_comment = CommentPicture(commentator=user, context=comment_detail, content=picture, created_time=comment_time)
	try:
		db.session.add(new_comment)
		db.session.commit()
		return jsonify({'message':'成功添加评论'})
	except:
		db.session.rollback()
		return jsonify({'message':'评论失败'}),405
