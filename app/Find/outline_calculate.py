from flask import g,request,jsonify
from app.models import *
from . import find
import math
from .. import config

@find.route('/update_hot')
def upload_hot():
    all_picture = Picture.query.all()
    request_time = datetime.now()
    pictures = {}
    for picture in all_picture:
        score = math.log((0.3 * picture.clicks + 0.2 * picture.stars.count()
                          + 0.3 * picture.comments.count() + 0.2 * picture.share_count) / 4) + (
                        request_time - config.base_time).seconds / 36000
        pictures[picture.id] = score
    order_set = sorted(pictures.items(), key=lambda e:e[1],reverse=True)
    picture_ids = dict(order_set).keys()
    # 给order
    order = 1
    for pic in picture_ids:
        pictures[pic] = order
        order = order + 1
    old_hot =  HotOrder.query.all()
    old_hotids = []
    for old in old_hot:
        old_hotids.append(old.picture_id)
    # 依然在榜但需要更新排位的
    need_update = list(set(picture_ids).intersection(set(old_hotids)))
    upgrade_hot = HotOrder.query.filter(HotOrder.picture_id.in_(need_update)).all()
    for up in upgrade_hot:
        up.order = pictures[up.picture.id]
        try:
            db.session.add(order)
            db.session.commit()
        except:
            db.session.rollback()
            return 'failure'
    # 离开榜单的
    need_delete = list(set(old_hotids).difference(set(need_update)))
    delete_hot = HotOrder.query.filter(HotOrder.picture_id.in_(need_delete)).all()
    # 删除离开榜单的内容
    for de in delete_hot:
        try:
            db.session.delete(de)
            db.session.commit()
        except:
            db.session.rollback()
            return 'failure'
    # 增加新进的内容
    need_add = list(set(picture_ids).difference(set(need_update)))
    for add in need_add:
        new_add = HotOrder(picture_ids=add,order=pictures['add'])
        try:
            db.session.add(order)
            db.session.commit()
        except:
            db.session.rollback()
            return 'failure'
    return 'ok'
