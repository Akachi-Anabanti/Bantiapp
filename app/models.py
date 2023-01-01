from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
from app.search import add_to_index, remove_from_index, query_index
import json
import redis
import rq
from flask import current_app
import uuid
from markdown import markdown
import bleach


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return (
            cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)),
            total,
        )

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted),
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes["add"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["update"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["delete"]:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, "before_commit", SearchableMixin.before_commit)
db.event.listen(db.session, "after_commit", SearchableMixin.after_commit)


followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)

p_likes = db.Table(
    "p_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
)


c_likes = db.Table(
    "c_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column(
        "comment_id",
        db.Integer,
        db.ForeignKey("comment.id"),
    ),
)


class User(db.Model, UserMixin):
    __searchable__ = ["username"]
    uid = db.Column(db.String(32), unique=True)
    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(128))
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship(
        "Post", backref="author", lazy="dynamic", cascade="all, delete"
    )

    comments = db.relationship(
        "Comment", backref="author", lazy="dynamic", cascade="all, delete"
    )

    last_message_read_time = db.Column(db.DateTime)

    last_notification_checked_time = db.Column(db.DateTime)

    liked_post = db.relationship(
        "Post",
        secondary=p_likes,
        primaryjoin=(p_likes.c.user_id == id),
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete",
    )
    liked_comment = db.relationship(
        "Comment",
        secondary=c_likes,
        primaryjoin=(c_likes.c.user_id == id),
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete",
    )

    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete",
    )

    messages_sent = db.relationship(
        "Message",
        foreign_keys="Message.sender_id",
        backref="author",
        lazy="dynamic",
        cascade="all, delete",
    )

    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic",
        cascade="all, delete",
    )

    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete"
    )

    pusher_notifications_created = db.relationship(
        "PusherNotification",
        foreign_keys="PusherNotification.source_id",
        backref="source",
        lazy="dynamic",
        cascade="all, delete",
    )
    pusher_notifications_received = db.relationship(
        "PusherNotification",
        foreign_keys="PusherNotification.target_id",
        backref="target",
        lazy="dynamic",
        cascade="all, delete",
    )

    tasks = db.relationship("Task", backref="user", lazy="dynamic")
    # Notification helper methods
    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_pusher_notifications(self):
        last_checked_time = self.last_notification_checked_time or datetime(1900, 1, 1)
        return (
            PusherNotification.query.filter_by(target=self)
            .filter(PusherNotification.timestamp > last_checked_time)
            .count()
        )

    # MESSAGES
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Message.query.filter_by(recipient=self)
            .filter(Message.timestamp > last_read_time)
            .count()
        )

    # PASSWORD Methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def set_uid(self):
        self.uid = uuid.uuid4().hex

    # FOLLOWINGS
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)

        own = Post.query.filter_by(user_id=self.id)

        return followed.union(own).order_by(Post.timestamp.desc())

    # POST AND COMMENT LIKES HELPERS METHODS
    def liked_posts(self):
        liked = Post.query.join(p_likes, (p_likes.c.user_id == Post.user_id)).filter(
            p_likes.c.user_id == self.id
        )
        return liked

    def like_p(self, post):
        if not self.liked_p(post):
            self.liked_post.append(post)

    def unlike_p(self, post):
        if self.liked_p(post):
            self.liked_post.remove(post)

    def liked_p(self, post):
        return self.liked_post.filter(p_likes.c.post_id == post.id).count() > 0

    def liked_comments(self):
        liked = Comment.query.join(
            c_likes, (c_likes.c.user_id == Comment.user_id)
        ).filter(c_likes.c.user_id == self.id)
        return liked

    def like_c(self, comment):
        if not self.liked_c(comment):
            self.liked_comment.append(comment)

    def unlike_c(self, comment):
        if self.liked_c(comment):
            self.liked_comment.remove(comment)

    def liked_c(self, comment):
        return self.liked_comment.filter(c_likes.c.comment_id == comment.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue(
            "app.tasks." + name, self.id, *args, **kwargs
        )
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self, complete=False).first()

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return
        return User.query.get(id)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Post(db.Model):
    __searchable__ = ["body"]
    pid = db.Column(db.String(32), unique=True)
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body_html = db.Column(db.Text)
    comments = db.relationship(
        "Comment", backref="post", lazy="dynamic", cascade="all, delete"
    )

    def get_comments(self):
        return Comment.query.filter_by(post_id=self.id, parent_id=None).all()

    def set_pid(self):
        self.pid = uuid.uuid4().hex

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = [
            "a",
            "abbr",
            "acronymn",
            "b",
            "blockquote",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "pre",
            "strong",
            "ul",
            "h1",
            "h2",
            "h3",
            "p",
        ]
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format="html"), tags=allowed_tags, strip=True
            )
        )

    def __repr__(self) -> str:
        return f"<Post {self.body}>"


db.event.listen(Post.body, "set", Post.on_changed_body)


class Comment(db.Model):
    __searchable__ = ["body"]
    __tablename__ = "comment"
    cid = db.Column(db.String(32), unique=True)
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"))

    replies = db.relationship(
        "Comment",
        backref=db.backref("reply", remote_side="Comment.id", cascade="all, delete"),
        lazy="dynamic",
    )

    def set_cid(self):
        self.cid = uuid.uuid4().hex

    def __repr__(self) -> str:
        return f"<Comment {self.body}>"


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self) -> str:
        return "<Message {}>".format(self.body)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        return json.loads(str(self.payload_json))


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get("progress", 0) if job is not None else 100


class PusherNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    action = db.Column(db.String(128))
    source_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    target_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
