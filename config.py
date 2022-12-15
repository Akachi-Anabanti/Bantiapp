import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config(object):
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "b\x0e\xfe\xe8\x1f#\xe8\xacR\x89\x91\x958\x10^\x89'\x18\x07\x97\xb4X\x9cR^\xf4\xb3 C\x12Aj6\xb5\xdb\xf2iFmBQ\xc7k,o\xd2\xab:\x03Z2\x17\xb1\x03f\x82j\xbaw\xb74\xee\xf6\x8d\x8c"
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URI"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = ["akachi.anabanti@outlook.com"]
    POST_PER_PAGE = 5
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


class DevelopmentConfig(Config):
    pass


class TestingConfig(Config):
    pass


class ProductionConfig(Config):
    pass


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
