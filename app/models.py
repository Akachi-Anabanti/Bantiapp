from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
from app import app
import jwt
from app.search import add_to_index, remove_from_index, query_index
import json
import numpy as np


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

likes = db.Table(
    "likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id")),
    db.Column("comment_id", db.Integer, db.ForeignKey("comment.id")),
)


class User(SearchableMixin, db.Model, UserMixin):
    __searchable__ = ["username"]
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy="dynamic")

    comments = db.relationship("Comment", backref="author", lazy="dynamic")

    last_message_read_time = db.Column(db.DateTime)

    liked_post = db.relationship(
        "Post",
        secondary=likes,
        primaryjoin=(likes.c.user_id == id),
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
    )
    liked_comment = db.relationship(
        "Comment",
        secondary=likes,
        primaryjoin=(likes.c.user_id == id),
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
    )

    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic"
    )

    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic",
    )

    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    # Notification helper methods
    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

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

    # FOLLOWERS
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
        liked = Post.query.join(likes, (likes.c.user_id == Post.user_id)).filter(
            likes.c.user_id == self.id
        )
        return liked

    def like(self, post):
        if not self.liked(post):
            self.liked_post.append(post)

    def unlike(self, post):
        if self.liked(post):
            self.liked_post.remove(post)

    def liked(self, post):
        return self.liked_post.filter(likes.c.post_id == post.id).count() > 0

    def liked_comments(self):
        liked = Comment.query.join(likes, (likes.c.user_id == Comment.user_id)).filter(
            likes.c.user_id == self.id
        )
        return liked

    def like_comment(self, comment):
        if not self.liked(comment):
            self.liked_comment.append(comment)

    def unlike_comment(self, comment):
        if self.liked(comment):
            self.liked_post.remove(comment)

    def comment_liked(self, comment):
        return self.liked_comment.filter(likes.c.post_id == comment.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])[
                "reset_password"
            ]
        except:
            return
        return User.query.get(id)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Post(SearchableMixin, db.Model):
    __searchable__ = ["body"]
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    comments = db.relationship("Comment", backref="post", lazy="dynamic")

    def get_comments(self):
        return Comment.query.filter_by(post_id=self.id, parent_id=None).all()

    def __repr__(self) -> str:
        return f"<Post {self.body}>"


class Comment(SearchableMixin, db.Model):
    __searchable__ = ["body"]
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"))

    replies = db.relationship(
        "Comment",
        backref=db.backref("reply", remote_side="Comment.id", uselist=False),
    )

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


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
