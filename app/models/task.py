from typing import Optional, Dict, Any
import redis
import rq
from flask import current_app
from datetime import datetime

from app import db


class Task(db.Model):
    """Task model for background jobs."""
    
    __tablename__ = "task"

    id: str = db.Column(db.String(36), primary_key=True)
    name: str = db.Column(db.String(128), index=True, nullable=False)
    description: str = db.Column(db.String(256))
    user_id: int = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False
    )
    complete: bool = db.Column(db.Boolean, default=False)
    failed: bool = db.Column(db.Boolean, default=False)
    error_message: Optional[str] = db.Column(db.Text)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    started_at: Optional[datetime] = db.Column(db.DateTime)
    completed_at: Optional[datetime] = db.Column(db.DateTime)

    def get_rq_job(self) -> Optional[rq.job.Job]:
        """Get the RQ job instance for this task."""
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self) -> int:
        """Get task progress percentage."""
        job = self.get_rq_job()
        return job.meta.get("progress", 0) if job is not None else 100

    def get_status(self) -> str:
        """Get the current status of the task."""
        if self.complete:
            return "completed"
        if self.failed:
            return "failed"
        if self.started_at and not self.completed_at:
            return "in_progress"
        return "queued"

    def set_failed(self, error_message: str) -> None:
        """Mark the task as failed with an error message."""
        self.failed = True
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'complete': self.complete,
            'failed': self.failed,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.get_progress(),
            'status': self.get_status()
        }

    def __repr__(self) -> str:
        return f"<Task {self.name}>"