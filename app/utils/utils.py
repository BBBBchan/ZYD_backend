from app.models import db, PushMessage
from app.config import logger
from flask import abort, request


def upload_avatar_v1(file):
    """
    上传图片至服务器
    :param file: 图片文件对象
    :return: url: 图片存储在服务器的网络路径
    """
    file_path = '../static/avatar/' + file.filename  # need change this
    with open(file_path, 'wb') as f:
        f.write(file.read())
    from flask import url_for
    url = 'http://127.0.0.1:5000' + url_for("static", filename="avatar/{}".format(file.filename))
    return url


def db_handler(instance):
    try:
        db.session.add(instance)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        abort(500)


def message_confirm(cls):
    msg_id = request.json.get('msg_id')
    if msg_id is None:
        abort(400)
    message = cls.query.get_or_404(msg_id)
    message.status = True
    db_handler(message)


def set_value_from_request(instance, data, args):
    for arg in args:
        temp = data.get(arg)
        if temp is None:
            abort(400)
            break
        setattr(instance, arg, temp)
    db_handler(instance)


def push_message_to_user(receiver_id, content):
    try:
        message = PushMessage(receiver_id=receiver_id, content=content)
    except Exception as e:
        logger.error(e)
        abort(500)
    db_handler(message)
