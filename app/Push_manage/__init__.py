from flask import Blueprint

pictrue_manage_blueprint = Blueprint('push_manage_blueprint', __name__)

from . import views