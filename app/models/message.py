from datetime import datetime
from typing import Dict

from app import db


class Message(db.Model):
    """Message model for user-to-user messages."""
    
    __tablename__ = "message"

    id: int = db.Column(db.Integer, primary_key=True)
    body: str = db.Column(db.String(500), nullable=False)
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sender_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    recipient_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    read_at: datetime = db.Column(db.DateTime)

    def mark_as_read(self) -> None:
        """Mark the message as read."""
        if not self.read_at:
            self.read_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert message to dictionary representation."""
        return {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp.isoformat(),
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

    def __repr__(self) -> str:
        return f"<Message {self.id}>"