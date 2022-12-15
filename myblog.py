from app import create_app, db
from app.models import User, Post, Comment, Message, Notification, Task

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Post": Post,
        "Comment": Comment,
        "Message": Message,
        "Notification": Notification,
        "Task": Task,
    }
