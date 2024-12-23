from app import db

# Association tables
followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
)

post_likes = db.Table(
    "post_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
    db.Column("post_id", db.Integer, db.ForeignKey("post.id", ondelete="CASCADE")),
)

comment_likes = db.Table(
    "comment_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE")),
    db.Column("comment_id", db.Integer, db.ForeignKey("comment.id", ondelete="CASCADE")),
)