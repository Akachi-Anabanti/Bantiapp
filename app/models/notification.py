from datetime import datetime
from typing import Dict, Any, Optional
import json

from app import db


class Notification(db.Model):
    """Notification model for user notifications."""
    
    __tablename__ = "notification"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(128), index=True, nullable=False)
    user_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    timestamp: float = db.Column(db.Float, index=True, default=datetime.utcnow().timestamp)
    payload_json: str = db.Column(db.Text, nullable=False)
    read_at: datetime = db.Column(db.DateTime)

    def get_data(self) -> Dict[str, Any]:
        """Get notification data from JSON payload."""
        return json.loads(str(self.payload_json))

    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        if not self.read_at:
            self.read_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'timestamp': self.timestamp,
            'data': self.get_data(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

    def __repr__(self) -> str:
        return f"<Notification {self.name}>"


class PusherNotification(db.Model):
    """Model for real-time push notifications."""
    
    __tablename__ = "pusher_notification"

    id: int = db.Column(db.Integer, primary_key=True)
    action: str = db.Column(db.String(128), nullable=False)
    source_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    target_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    read_at: datetime = db.Column(db.DateTime)
    data: Optional[str] = db.Column(db.Text)  # Additional JSON data if needed

    def mark_as_read(self) -> None:
        """Mark the push notification as read."""
        if not self.read_at:
            self.read_at = datetime.utcnow()

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Get additional data if present."""
        return json.loads(self.data) if self.data else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert push notification to dictionary representation."""
        return {
            'id': self.id,
            'action': self.action,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'timestamp': self.timestamp.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'data': self.get_data()
        }

    def __repr__(self) -> str:
        return f"<PusherNotification {self.action}>"