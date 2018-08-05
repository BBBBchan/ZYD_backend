from flask import Blueprint

picture_blueprint = Blueprint('picture_blueprint', __name__)

from . import views, forms