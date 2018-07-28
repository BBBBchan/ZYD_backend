from flask import Blueprint
from ..models import *

video_blueprint = Blueprint('video_blueprint', __name__)

# @video_blueprint.route('/video_list')
# def video_list():
