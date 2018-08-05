import os
from flask import Flask
from app.models import db
from .user.views import user_blueprint
from .video import video_blueprint
from .picture import picture_blueprint
from .showCase.views import showcase_blueprint
from .order.views import order_blueprint
from .comment.views import comment_blueprint
from .admin.views import admin_blueprint


def create_app(object_name):
    app = Flask(__name__)
    app.config.from_object(object_name)

    db.init_app(app)

    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(video_blueprint, url_prefix='/video')
    app.register_blueprint(picture_blueprint, url_prefix='/picture')
    app.register_blueprint(showcase_blueprint, url_prefix='/showcase')
    app.register_blueprint(order_blueprint, url_prefix='/order')
    app.register_blueprint(comment_blueprint, url_prefix='/comment')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app


env = os.environ.get('APP_ENV', 'dev')
app = create_app('app.config.%sConfig' % env.capitalize())
