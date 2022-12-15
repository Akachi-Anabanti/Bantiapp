from . import fd
from flask import current_app


@fd.route("/feed")
def feed():
    return "......"
