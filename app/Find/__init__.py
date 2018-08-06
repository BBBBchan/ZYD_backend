from flask import Blueprint

find = Blueprint('find', __name__)

from . import views