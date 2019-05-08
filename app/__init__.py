import logging
import os

from flask import Flask

from app.models import db
from .admin.views import admin_blueprint
from .comment.views import comment_blueprint
from .order.views import order_blueprint
from .picture import picture_blueprint
from .user.views import user_blueprint
from .video import video_blueprint
from .picture import picture_blueprint
from .showCase.views import showcase_blueprint
from .user.views import user_blueprint
from .video import video_blueprint
from .Picture_manage import pictrue_manage_blueprint
from .Push_manage import push_manage_blueprint
from .Find import find


def create_app(object_name):
    app = Flask(__name__)
    app.config.from_object(object_name)

    db.init_app(app)
    db.app = app
    db.create_all()

    app.register_blueprint(user_blueprint, url_prefix='/api/user')
    app.register_blueprint(video_blueprint, url_prefix='/api/video')
    app.register_blueprint(picture_blueprint, url_prefix='/api/picture')
    app.register_blueprint(showcase_blueprint, url_prefix='/api/showcase')
    app.register_blueprint(order_blueprint, url_prefix='/api/order')
    app.register_blueprint(comment_blueprint, url_prefix='/api/comment')
    app.register_blueprint(admin_blueprint, url_prefix='/api/admin')
    app.register_blueprint(pictrue_manage_blueprint, url_prefix='/api/picture_manage')
    app.register_blueprint(push_manage_blueprint, url_prefix='/api/push_manage')
    app.register_blueprint(find, url_prefix='/api/find/')

    return app


env = os.environ.get('APP_ENV', 'dev')
app = create_app('app.config.%sConfig' % env.capitalize())


logging.basicConfig(filename='./log/app.log',
                    format='[%(asctime)s][%(filename)s][line:%(lineno)d][%(levelname)s] %(message)s')
