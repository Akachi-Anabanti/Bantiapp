from __future__ import annotations
from datetime import datetime
from typing import Any, List
from uuid import uuid4

from bleach import clean, linkify
from markdown import markdown
from sqlalchemy import event

from app import db
from .mixins import SearchableMixin
from . import *

class Post(SearchableMixin, db.Model):
    """Post model for user posts."""
    
    __tablename__ = "post"
    __searchable__ = ["body"]

    id: int = db.Column(db.Integer, primary_key=True)
    pid: str = db.Column(db.String(32), unique=True, nullable=False)
    body: str = db.Column(db.String(500), nullable=False)
    body_html: str = db.Column(db.Text)
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    comments = db.relationship(
        "Comment",
        backref="post",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize post and set UUID."""
        super().__init__(**kwargs)
        if not self.pid:
            self.pid = uuid4().hex

    def get_comments(self) -> List[Comment]:
        """Get top-level comments."""
        return Comment.query.filter_by(
            post_id=self.id,
            parent_id=None
        ).all()

    @staticmethod
    def on_changed_body(target: Post, value: str, oldvalue: str, initiator: Any) -> None:
        """Convert Markdown to HTML when body changes."""
        allowed_tags = [
            "a", "abbr", "acronym", "b", "blockquote", "code",
            "em", "i", "li", "ol", "pre", "strong",
            "ul", "h1", "h2", "h3", "p"
        ]
        target.body_html = linkify(clean(
            markdown(value, output_format="html"),
            tags=allowed_tags,
            strip=True
        ))

    def __repr__(self) -> str:
        return f"<Post {self.id}>"


# Set up event listener for Post body changes
event.listen(Post.body, "set", Post.on_changed_body)