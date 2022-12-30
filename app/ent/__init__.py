from flask import Blueprint

et = Blueprint("extra", __name__)

from app.ent import routes
