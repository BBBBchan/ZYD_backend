from flask import Blueprint

comment_blueprint = Blueprint('comment_blueprint', __name__)

from . import views, forms