from . import comment_blueprint
import json
from flask import current_app,  request, jsonify, g
from app.middlewares import checkLogin
from app.models import User, CommentPicture, datetime, db, Permission, Picture
from app.config import *

#获取评论列表
@comment_blueprint.route('/comment_list', methods=['GET','POST'])					
@checkLogin
def comment_list():
	data = request.json
	user_id = data.get('user_id')
	pic_id = data.get('pic_id')
	page_count = data.get('page_count', 10)
	page_num = data.get('page_num', 1)
	
	if pic_id == None or user_id == None:							
		return jsonify({'message':'用户或图片信息不能为空'}), 400
	comment_all = CommentPicture.query.filter_by(content_id = pic_id).all()
	if len(comment_all) == 0:
		return jsonify({'message':'未找到相应评论'}), 404
	res = []
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
@comment_blueprint.route('/comment_modify', methods=['GET', 'POST'])					
@checkLogin
def comment_modify():
	data = request.json
	comment_id = data.get('comment_id')
	user_id = data.get('user_id')
	pic_id = data.get('pic_id')
	comment_detail = data.get('comment_detail')

	try:	
		comment = CommentPicture.query.filter_by(id=comment_id,content_id=pic_id,commentator_id=user_id).first()
		if comment.context == comment_detail:
			return jsonify({'message':'评论内容未修改'}),401
		else:
			comment.context = comment_detail
			try:
				db.session.commit()
				return jsonify({'message':'修改评论成功'})
			except:
				dn.session.rollback()
				return jsonify({'message':'修改评论失败'})
	except:
		db.session.rollback()
		return jsonify({'message':'获取评论失败'}),400

#删除评论
@comment_blueprint.route('/comment_delete', methods=['GET','POST'])						
@checkLogin
def comment_delete():
	data = request.json
	comment_id = data.get('comment_id')
	user_id = data.get('user_id')
	pic_id = data.get('pic_id')

	try:	
		comment = CommentPicture.query.filter_by(id=comment_id, content_id=pic_id, commentator_id=user_id).first()
		try:
			db.session.delete(comment)
			db.session.commit()
			return jsonify({'message':'删除成功'})
		except:
			db.session.rollback()
			return jsonify({'message':'删除失败'}),400
	except:
		db.session.rollback()
		return jsonify({'message':'获取评论失败'}),401

#添加评论
@comment_blueprint.route('/comment_upload', methods=['POST'])							
@checkLogin
def comment_upload():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'用户名不能为空'}),400
	pic_id = data.get('pic_id')
	if pic_id == None:
		return jsonify({'message':'未找到相应图片'}),401
	comment_detail = data.get('comment_detail')
	if comment_detail == None:
		return jsonify({'message':'评论内容不能为空'}),402	
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
