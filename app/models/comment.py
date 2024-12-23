from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from app import db
from .mixins import SearchableMixin


class Comment(SearchableMixin, db.Model):
    """Comment model for post comments."""
    
    __tablename__ = "comment"
    __searchable__ = ["body"]

    id: int = db.Column(db.Integer, primary_key=True)
    cid: str = db.Column(db.String(32), unique=True, nullable=False)
    body: str = db.Column(db.Text, nullable=False)
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id: int = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id: int = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    parent_id: Optional[int] = db.Column(db.Integer, db.ForeignKey("comment.id"))

    # Relationship for nested comments
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize comment and set UUID."""
        super().__init__(**kwargs)
        if not self.cid:
            self.cid = uuid4().hex

    def get_reply_count(self) -> int:
        """Get the total number of replies to this comment."""
        return self.replies.count()

    def get_thread_depth(self) -> int:
        """Calculate how deep this comment is in a thread."""
        depth = 0
        current = self
        while current.parent is not None:
            depth += 1
            current = current.parent
        return depth

    def __repr__(self) -> str:
        return f"<Comment {self.id}>"