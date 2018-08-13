from flask import Blueprint

find = Blueprint('find', __name__)

# 发现，广场，推荐页面的相关接口

from . import views,outline_calculate