class Config(object):
    pass


class ProdConfig(object):
    pass


class DevConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # OSS OPEN IP
    OSS_URL = ''
    
    
APP_ID = 'wxdea953f5e8d0c0d6'
APP_SECRET = '3ced46fd7e962e3eb92a82fa7348ef44'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 1