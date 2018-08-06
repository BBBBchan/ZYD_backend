from app.config import APP_ID, APP_SECRET, REDIS_HOST, REDIS_PORT, REDIS_DB, logger
import requests
import redis
import uuid


redis_service = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                                  db=REDIS_DB, decode_responses=True)


def get_session_key_and_openid(code):
    """
    前端返回code，通过微信官方api使用code换取session_key和openid
    :param code
    :return: session_key, openid
    """
    req = requests.get('https://api.weixin.qq.com/sns/jscode2session?'
                       'appid={APP_ID}&secret={SECRET}&js_code={CODE}&grant_type=authorization_code'
                       .format(APP_ID=APP_ID, SECRET=APP_SECRET, CODE=code))
    data = req.json()
    session_key = data.get('session_key')
    openid = data.get('openid')
    return session_key, openid


def generate_3rd_session(session_key, openid):
    """
    基于MAC地址和时间生成唯一的token作为用户认证标识
    将此标识作为key, 用户的session_key和openid拼接在一起作为value存在redis中
    :param session_key
    :param openid
    :return: key
    """
    key = uuid.uuid1()
    value = session_key + ',' + openid
    redis_service.set(key, value)
    return key


def get_token_value(token):
    """
    获取存在redis中token所对应的value
    :param token
    :return: session_key, openid
    """
    value = redis_service.get(token)
    session_key, openid = value.split(',')
    return session_key, openid


def update_token(token):
    """
    更新用户认证的token
    :param token
    :return: new_token
    """
    value = redis_service.get(token)
    session_key, openid = value.split(',')
    redis_service.delete(token)
    new_token = generate_3rd_session(session_key, openid)
    return new_token
