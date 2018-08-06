import logging.config
from os import path


class Config(object):
    pass


class ProdConfig(object):
    pass


class DevConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


# oss 暂时用我的(zsj),尽快换填成工作室的
OSS_OPEN_IP = 'sereph.oss-cn-beijing.aliyuncs.com'
OSS_end_point = 'oss-cn-beijing.aliyuncs.com'

# 微信小程序配置
APP_ID = 'wxdea953f5e8d0c0d6'
APP_SECRET = '3ced46fd7e962e3eb92a82fa7348ef44'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 1

path = path.join(path.dirname(path.abspath(__file__)), 'logger.conf')
logging.config.fileConfig(path)
logger = logging.getLogger('debug')
