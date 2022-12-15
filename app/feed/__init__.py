from flask import Blueprint

fd = Blueprint("fd", __name__)

from app.feed import routes
