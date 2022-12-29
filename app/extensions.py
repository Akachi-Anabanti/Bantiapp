from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
from flask_pusher import Pusher
from flask_pagedown import PageDown


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
moment = Moment()
bable = Babel()
pusher = Pusher()
pagedown = PageDown()
login.login_view = "auth.login"
login.login_message = "Please login to access this page"
