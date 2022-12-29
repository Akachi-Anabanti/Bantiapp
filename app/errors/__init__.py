from flask import Blueprint

err = Blueprint("errors", __name__)

from app.errors import handlers
