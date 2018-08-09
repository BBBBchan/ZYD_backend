from flask import Blueprint
showcase_blueprint = Blueprint('showcase_blueprint', __name__)
from . import views, forms