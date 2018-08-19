"""
图片相关后台管理
"""
from flask import Blueprint

pictrue_manage_blueprint = Blueprint('picture_manage_blueprint', __name__)

from . import views