from __future__ import annotations
from datetime import datetime
from typing import Any, Optional, List, Dict
from uuid import uuid4

from flask import current_app
from flask_login import UserMixin
from hashlib import md5
import jwt
import json

from app import db, login
from .mixins import SearchableMixin
from .tables import followers, post_likes, comment_likes
from werkzeug.security import generate_password_hash, check_password_hash
from . import *

class User(SearchableMixin, UserMixin, db.Model):
    """User model representing application users."""
    
    __tablename__ = "user"
    __searchable__ = ["username"]

    id: int = db.Column(db.Integer, primary_key=True)
    uid: str = db.Column(db.String(32), unique=True, nullable=False)
    full_name: str = db.Column(db.String(128))
    username: str = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email: str = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash: str = db.Column(db.String(128), nullable=False)
    about_me: str = db.Column(db.String(500))
    last_seen: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    member_since: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_read_time: datetime = db.Column(db.DateTime)
    last_notification_checked_time: datetime = db.Column(db.DateTime)

    # Relationships
    posts = db.relationship(
        "Post",
        backref="author",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    comments = db.relationship(
        "Comment",
        backref="author",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    liked_posts = db.relationship(
        "Post",
        secondary=post_likes,
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete"
    )
    
    liked_comments = db.relationship(
        "Comment",
        secondary=comment_likes,
        backref=db.backref("likes", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete"
    )
    
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
        cascade="all, delete"
    )

   # User methods
    def __init__(self, **kwargs: Any) -> None:
        """Initialize user and set UUID."""
        super().__init__(**kwargs)
        if not self.uid:
            self.uid = uuid4().hex

    @property
    def avatar_url(self) -> str:
        """Generate Gravatar URL for user."""
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s=128"

    def set_password(self, password: str) -> None:
        """Set hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def follow(self, user: User) -> None:
        """Follow another user."""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user: User) -> None:
        """Unfollow a user."""
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user: User) -> bool:
        """Check if following a user."""
        return self.followed.filter(
            followers.c.followed_id == user.id
        ).count() > 0

    def followed_posts(self):
        """Get posts from followed users plus own posts."""
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def like_post(self, post: 'Post') -> None:
        """Like a post."""
        if not self.has_liked_post(post):
            self.liked_posts.append(post)

    def unlike_post(self, post: 'Post') -> None:
        """Unlike a post."""
        if self.has_liked_post(post):
            self.liked_posts.remove(post)

    def has_liked_post(self, post: 'Post') -> bool:
        """Check if user has liked a post."""
        return self.liked_posts.filter(
            post_likes.c.post_id == post.id
        ).count() > 0

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        """Generate password reset token."""
        return jwt.encode(
            {
                "reset_password": self.id,
                "exp": datetime.utcnow().timestamp() + expires_in
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

    @staticmethod
    def verify_reset_password_token(token: str) -> Optional[User]:
        """Verify password reset token."""
        try:
            id = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )["reset_password"]
        except:
            return None
        return User.query.get(id)

    def add_notification(self, name: str, data: Dict) -> Notification:
        """Add a notification for the user."""
        self.notifications.filter_by(name=name).delete()
        notification = Notification(
            name=name,
            payload_json=json.dumps(data),
            user=self
        )
        db.session.add(notification)
        return notification

    def launch_task(self, name: str, description: str, *args: Any, **kwargs: Any) -> Task:
        """Launch a background task."""
        rq_job = current_app.task_queue.enqueue(
            f"app.tasks.{name}", 
            self.id,
            *args,
            **kwargs
        )
        task = Task(
            id=rq_job.get_id(),
            name=name,
            description=description,
            user=self
        )
        db.session.add(task)
        return task

    def get_tasks_in_progress(self) -> List[Task]:
        """Get all incomplete tasks."""
        return Task.query.filter_by(
            user=self,
            complete=False
        ).all()

    def get_task_in_progress(self, name: str) -> Optional[Task]:
        """Get specific incomplete task."""
        return Task.query.filter_by(
            name=name,
            user=self,
            complete=False
        ).first()

    def __repr__(self) -> str:
        return f"<User {self.username}>"

@login.user_loader
def load_user(id: str) -> Optional[User]:
    """Load user by ID for Flask-Login."""
    try:
        return User.query.get(int(id))
    except ValueError:
        return None