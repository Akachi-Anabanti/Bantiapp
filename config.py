import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a892d34c873011edb8225c3a4547d4d8"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("SENDGRID_API_KEY")
    ADMINS = ["akachi.anabanti@outlook.com"]
    MAIL_DEFAULT_SENDER = ADMINS[0]
    POST_PER_PAGE = 20
    COMMENTS_PER_PAGE = 5
    ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL")
    ELASTICSEARCH_USERNAME = os.environ.get("ELASTICSEARCH_USERNAME")
    HTTP_CERT = os.path.join(basedir, "http_ca.crt")
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://"
    PUSHER_APP_ID = os.environ.get("PUSHER_APP_ID")
    PUSHER_SECRET = os.environ.get("PUSHER_SECRET")
    PUSHER_KEY = os.environ.get("PUSHER_KEY")
    PUSHER_CLUSTER = os.environ.get("PUSHER_CLUSTER")

    @staticmethod
    def init_app(app):
        # used to initialize the coonfig in create_app()
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "data-dev.sqlite")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URI") or "sqlite://"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace(
        "postgres://", "postgresql://"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")


class HerokuConfig(ProductionConfig):

    pass


class DigitalOceanConfig(ProductionConfig):
    pass


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
    "heroku": HerokuConfig,
    "digitalocean": DigitalOceanConfig,
}
