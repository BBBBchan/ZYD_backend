from flask import Blueprint

video_blueprint = Blueprint('video_blueprint', __name__)

from . import  views, forms