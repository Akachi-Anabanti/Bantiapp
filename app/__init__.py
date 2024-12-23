from flask import Flask
from config import config
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from elasticsearch import Elasticsearch
from app.extensions import db, migrate, login, mail, moment, pusher, pagedown #bable, 
from redis import Redis
import rq


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Extensions initialization

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    # bable.init_app(app)
    pagedown.init_app(app)
    if not app.debug:
        pusher.init_app(
        app,
        app_id=app.config["PUSHER_APP_ID"],
        key=app.config["PUSHER_KEY"],
        secret=app.config["PUSHER_SECRET"],
        cluster=app.config["PUSHER_CLUSTER"],
        ssl=True,
    )

    if not app.debug:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="Bantiapp Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/bantiapp.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Bantiapp startup")

    app.elasticsearch = (
        Elasticsearch(
            [app.config["ELASTICSEARCH_URL"]],
            ca_certs=app.config["HTTP_CERT"],
            basic_auth=(
                app.config["ELASTICSEARCH_USERNAME"],
                app.config["ELASTICSEARCH_PASSWORD"],
            ),
        )
        if app.config["ELASTICSEARCH_URL"]
        else None
    )

    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue("bantiapp-tasks", connection=app.redis)

    from app.authentication import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    from app.main import main as main_bp

    app.register_blueprint(main_bp)
    from app.user import bp as user_bp

    app.register_blueprint(user_bp, url_prefix="/user")
    from app.errors import err as error_bp

    app.register_blueprint(error_bp)
    from app.feed import fd as feed_blueprint

    app.register_blueprint(feed_blueprint)
    from app.ent import et as extras_blueprint

    app.register_blueprint(extras_blueprint)

    return app
