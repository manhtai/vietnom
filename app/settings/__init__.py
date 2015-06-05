from flask import Blueprint

settings = Blueprint('settings', __name__)

from app.settings import views
