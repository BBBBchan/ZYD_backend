from app.config import APP_ID, APP_SECRET, REDIS_HOST, REDIS_PORT, REDIS_DB
import requests
import redis
import uuid


redis_service = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT,
                                  db=REDIS_DB, decode_responses=True)


def get_session_key_and_openid(code):
    req = requests.get('https://api.weixin.qq.com/sns/jscode2session?'
                       'appid={APP_ID}&secret={SECRET}&js_code={CODE}&grant_type=authorization_code'
                       .format(APP_ID=APP_ID, SECRET=APP_SECRET, CODE=code))
    data = req.json()
    session_key = data['session_key']
    openid = data['openid']
    return session_key, openid


def generate_3rd_session(session_key, openid):
    key = uuid.uuid1()
    value = session_key + ',' + openid
    redis_service.set(key, value)
    return key


def get_token_value(token):
    value = redis_service.get(token)
    session_key, openid = value.split(',')
    return session_key, openid


def update_token(token):
    value = redis_service.get(token)
    session_key, openid = value.split(',')
    redis_service.delete(token)
    new_token = generate_3rd_session(session_key, openid)
    return new_token
