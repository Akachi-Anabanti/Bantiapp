from typing import Any, List
from sqlalchemy import event
from sqlalchemy.orm import Session

from app import db
from app.search import add_to_index, remove_from_index, query_index


class SearchableMixin:
    """Mixin to add full-text search capabilities to models."""
    
    __searchable__: List[str] = []

    @classmethod
    def search(cls, expression: str, page: int, per_page: int) -> tuple[Any, int]:
        """
        Search for items matching the expression with pagination.
        
        Args:
            expression: Search query string
            page: Page number
            per_page: Items per page
            
        Returns:
            Tuple of (query results, total matches)
        """
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
            
        when = [(ids[i], i) for i in range(len(ids))]
        return (
            cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)),
            total,
        )

    @classmethod
    def before_commit(cls, session: Session) -> None:
        """Store changes before commit for search index updates."""
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session: Session) -> None:
        """Update search index after commit."""
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
    def reindex(cls) -> None:
        """Rebuild search index for all instances."""
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


# Set up SQLAlchemy event listeners for search indexing
event.listen(db.session, "before_commit", SearchableMixin.before_commit)
event.listen(db.session, "after_commit", SearchableMixin.after_commit)