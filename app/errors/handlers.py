from flask import render_template
from app import db
from . import err


@err.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@err.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500
