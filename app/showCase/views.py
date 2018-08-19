from . import showcase_blueprint
from flask import current_app,  request, jsonify, g
from app.middlewares import checkLogin
from app.models import *
from app.config import *

#创建作品集
@showcase_blueprint.route('/create_showcase', methods=['POST'])
@checkLogin
def create_showcase():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	showcase_name = data.get('showcase_name')
	if showcase_name == None:
		return jsonify({'message':'获取作品集名称失败'}),401
	showcase_description = data.get('showcase_description')
	if showcase_description == None:
		return jsonify({'message':'获取作品集描述失败'}),402
	pic_num = data.get('pic_num')
	if pic_num == None:
		return jsonify({'message':'获取图片数量失败'}),403
	elif pic_num == 0:
		return jsonify({'message':'未选择图片'}),404

	all_pic_id = data.get('all_pic_id')
	all_pic = []
	for i in range(0,pic_num):
		try:
			pic = Picture.query.filter_by(author_id=user_id,id=all_pic_id[i]).first()
			all_pic.append(pic)
		except:
			db.session.rollback()
			return jsonify({'message':'未找到图片'}),405
	
	created_time = str(datetime.now())
	new_showcase = ShowCase(name=showcase_name,description=showcase_description,created_time=created_time,author_id=user_id,pictures=all_pic)
	try:
		db.session.add(new_showcase)
		db.session.commit()
		return jsonify({'message':'创建成功'})
	except:
		db.session.rollback()
		return jsonify({'message':'创建失败'}),406

#删除整个作品集
@showcase_blueprint.route('/showcase_delete/<showcase_id>', methods=['GET','POST'])
@checkLogin
def showcase_delete(showcase_id):
	showcase = ShowCase.query.filter_by(id=showcase_id).first()
	try:
		db.session.delete(showcase)
		return jsonify({'message':'删除成功'})
	except:
		db.session.rollback()
		return jsonify({'message':'删除失败'}),400

#获取作品集列表
@showcase_blueprint.route('/showcase_list', methods=['POST'])
@checkLogin
def showcase_list():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	page_count = data.get('page_count',10)
	page_num = data.get('page_num',1)
	
	try:
		all_showcase = ShowCase.query.filter_by(author_id=user_id).all()
		if len(all_showcase) == 0:
			return jsonify({'message':'作品集数量为0'}),402
		res = {}
		for i in range(page_count*(page_num-1), page_count*page_num):
			showcase = {
				'showcase_id': all_showcase[i].id,
				'showcase_name': all_showcase[i].name,
				'showcase_description': all_showcase[i].description,
				'showcase_created_time': all_showcase[i].created_time,
				'first_pic_url': all_showcase[i].pictures[0].url,
			}
			res.append(showcase)
		return jsonify(res)

	except:
		return jsonify({'message':'获取作品集列表失败'}),401

#添加图片到作品集
@showcase_blueprint.route('/add_pic', methods=['POST'])
@checkLogin
def add_pic():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	showcase_id = data.get('showcase_id')
	if showcase_id == None:
		return jsonify({'message':'获取作品集id失败'}),401
	pic_num = data.get('pic_num')
	if pic_num == None:
		return jsonify({'message':'获取图片数量失败'}),402
	elif pic_num == 0:
		return jsonify({'message':'选择图片数量为0'}),403
	all_pic_id = data.get('all_pic_id')
	if all_pic_id == None:
		return jsonify({'message':'获取图片id失败'}),404
	try:
		showcase = ShowCase.query.filter_by(id=showcase_id).first()
	except:
		db.session.rollback()
		return jsonify({'message':'获取作品集失败'}),405
	for i in range(0, pic_num):
		try:
			pic = Picture.query.filter_by(id=all_pic_id[i], author_id=user_id).first()
		except:
			db.session.rollback()
			return jsonify({'message':'获取图片失败'}),406
		showcase.pictures.append(pic)
	
	try:
		db.session.commit()
		return jsonify({'message':'添加成功'})
	except:
		db.session.rollback()
		return jsonify({'message':'添加失败'}),407

#从作品集中删除图片
@showcase_blueprint.route('/delete_pic', methods=['POST'])
@checkLogin
def delete_pic():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	showcase_id = data.get('showcase_id')
	if showcase_id == None:
		return jsonify({'message':'获取作品集id失败'}),401
	pic_num = data.get('pic_num')
	if pic_num == None:
		return jsonify({'message':'获取图片数量失败'}),402
	elif pic_num == 0:
		return jsonify({'message':'选择图片数量为0'}),403
	all_pic_id = data.get('all_pic_id')
	if all_pic_id == None:
		return jsonify({'message':'获取图片id失败'}),404

	try:
		showcase = ShowCase.query.filter_by(id=showcase_id).first()
		for i in range(0,pic_num):
			for j in range(0,len(showcase.pictures)):
				if all_pic_id[i] == showcase.pictures[j].id:
					del showcase.pictures[j]		
		try:
			db.session.commit()
			return jsonify({'message':'删除成功'})
		except:
			db.session.rollback()
			return jsonify({'message':'删除失败'}),406
	except:
		return jsonify({'message','获取作品集失败'}),405

#获取作品集详情
@showcase_blueprint.route('/showcase_detail/<showcase_id>', methods=['GET', 'POST'])
@checkLogin
def showcase_detail(showcase_id):
	try:
		showcase = ShowCase.query.filter_by(id=showcase_id).first()
		res = {
			'showcase_id': showcase.id,
			'showcase_name': showcase.name,
			'showcase_description': showcase.description,
			'showcase_created_time': showcase.created_time,
			'pic_num': len(showcase.pictures),
		}
	except:
		db.session.rollback()
		return jsonify({'message':'获取作品集失败'}),400

	all_pic = {}
	for i in range(0,len(showcase.pictures)):
		try:
			picture = Picture.query.filter_by(id=showcase.pictures[i].id)
		except:
			db.session.rollback()
			return jsonify({'message':'未找到图片'}),401
		pic = {
			'pic_id':picture.id,
			'pic_name':picture.name,
			'pic_url':picture.url,

		}
		try:
			had_star = StarPicture.query.filter_by(content_id=picture.id).first()
			if had_star == None:
				pic['had_star'] = False
			else:
				pic['had_star'] = True
			pic['star_count'] = StarPicture.query.filter_by(content_id=picture.id).count()
			pic['comment_count'] = CommentPicture.query.filter_by(content_id=picture.id).count()
			all_pic[i] = pic
		except:
			db.session.rollback()
			return jsonify({'message':'获取点赞信息失败'}),402
		res['all_pic_info'] = all_pic 
		return jsonify(res)

#修改作品集基本信息
@showcase_blueprint.route('/showcase_modify', methods=['POST'])
@checkLogin
def showcase_modify():
	data = request.json
	user_id = data.get('user_id')
	if user_id == None:
		return jsonify({'message':'获取用户id失败'}),400
	showcase_id = data.get('showcase_id')
	if showcase_id == None:
		return jsonify({'message':'获取作品集id失败'}),401
	showcase_name = data.get('showcase_name')
	if showcase_name == None:
		return jsonify({'message':'获取作品集名称失败'}),402
	showcase_description = data.get('showcase_description')
	if showcase_description == None:
		return jsonify({'message':'获取作品集描述失败'}),403

	try:
		showcase = ShowCase.query.filter_by(id=showcase_id,author_id=user_id).first()
		if showcase_name == showcase.name and showcase_description == showcase.description:
			return jsonify({'message':'未修改任何内容'}),405
		else:
			showcase.name = showcase_name
			showcase.description = showcase_description
			try:
				db.session.commit()
				return jsonify({'message':'修改成功'})
			except:
				db.session.rollback()
				return jsonify({'message':'修改失败'}),406
	except:
		db.session.rollback()
		return jsonify({'message':'获取作品集失败'}),404
