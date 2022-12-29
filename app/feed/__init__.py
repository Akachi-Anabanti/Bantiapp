from flask import Blueprint

fd = Blueprint("fd", __name__, template_folder="templates", static_folder="static")

from app.feed import routes
