import requests
from app.models import db
from app.config import logger
from flask import abort
import datetime


def upload_avatar(file):
    """
    上传图片至图床
    :param file: 图片文件对象
    :return: url: 图床url
    """
    upload_api = 'https://sm.ms/api/upload'
    files = {'smfile': file}
    req = requests.post(upload_api, files=files)
    return req.json()['data']['url']


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