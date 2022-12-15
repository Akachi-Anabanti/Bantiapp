from . import main
from flask import (
    render_template,
    redirect,
    request,
    current_app,
    url_for,
    flash,
    g,
    jsonify,
)
from flask_login import login_required, current_user
from app.models import Post, Comment, Notification, User, Message
from app import db
from .forms import PostForm, CommentForm, MessageForm, SearchForm, EmptyForm
import os
from flask import send_from_directory
from datetime import datetime
from flask_babel import get_locale
from flask_moment import moment


@main.before_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()
        g.empty_form = EmptyForm()
    g.locale = str(get_locale())


@main.route("/explore")
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config["POST_PER_PAGE"], error_out=False
    )
    next_url = url_for(".explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for(".explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "main/index.html",
        title="Explore",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@main.route("/", methods=["POST", "GET"])
@main.route("/index", methods=["POST", "GET"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is live!")
        return redirect(url_for("main.index"))
    page = request.args.get("page", 1, type=int)

    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config["POST_PER_PAGE"], error_out=False
    )
    next_url = url_for("main.index", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("main.index", page=posts.prev_num) if posts.has_prev else None

    return render_template(
        "main/index.html",
        title="Home",
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@main.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post_detail(id):
    post = Post.query.get(id)
    form = CommentForm()
    if not post:
        flash("Post does not exist")
        return redirect(url_for("main.index"))
    comments = post.comments
    if request.method == "POST":
        modalbody = request.form.get("post-comment")
        if form.validate_on_submit():
            comment_body = form.comment.data
            new_comment = Comment(
                body=comment_body,
                author_id=current_user.id,
                post_id=id,
            )
            db.session.add(new_comment)
            new_comment.post = post
            db.session.commit()
        elif modalbody and modalbody.strip():
            comment_body = request.form.get("post-comment")
            new_comment = Comment(
                body=comment_body,
                author_id=current_user.id,
                post_id=id,
            )
            db.session.add(new_comment)
            new_comment.post = post
            db.session.commit()
        else:
            return redirect(url_for(".post_detail", id=id) + "#")
        return redirect(url_for(".post_detail", id=id) + "#" + str(new_comment.id))
    return render_template("main/post.html", form=form, comments=comments, post=post)


@main.route("/comment/reply", methods=["GET", "POST"])
@login_required
def reply():
    if request.method == "POST":
        form = CommentForm()
        if form.validate_on_submit():
            post_id = request.form.get("post_id")
            parent_id = request.form.get("parent")
            reply = Comment(
                body=form.comment.data,
                author_id=current_user.id,
                post_id=post_id,
                parent_id=parent_id,
            )
            db.session.add(reply)

            reply.post = Post.query.get(post_id)
            reply.comment = Comment.query.get(parent_id)
            db.session.commit()
            return redirect(url_for(".post_detail", id=post_id) + "#" + str(reply.id))
    return redirect(url_for(".index"))


@main.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for(".explore"))

    page = request.args.get("page", 1, type=int)
    posts, total = Post.search(
        g.search_form.q.data, page, current_app.config["POST_PER_PAGE"]
    )
    next_url = (
        url_for(".search", q=g.search_form.q.data, page=page + 1)
        if total > page * current_app.config["POST_PER_PAGE"]
        else None
    )
    prev_url = (
        url_for(".search", q=g.search_form.q.data, page=page - 1) if page > 1 else None
    )
    # return render_template(
    #     "main/search.html",
    #     title="Search",
    #     posts=posts,
    #     next_url=next_url,
    #     prev_url=prev_url,
    # )
    data = [
        {
            "username": post.author.username,
            "time": moment(post.timestamp).fromNow(refresh=True),
            "body": post.body,
            "id": post.id,
            "postUrl": url_for("main.post_detail", id=post.id),
            "userUrl": url_for("bp.user", username=post.author.username),
            "imgUrl": url_for("main.serve_photo", username=post.author.username),
        }
        for post in posts
    ]
    return jsonify(data)


@main.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())

    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )


@main.route("/like/<int:post_id>", methods=["POST", "GET"])
@login_required
def like(post_id):
    if request.method == "GET":
        return redirect(url_for(".index"))
    post = Post.query.get(post_id)
    if post is None:
        flash("post not found.")
        return redirect(url_for(".index"))
    if current_user == post.author:
        return redirect(url_for(".index"))
    current_user.like(post)
    db.session.commit()
    # current_app.pusher('blog', 'post_liked',)
    flash("You liked a post by {}".format(post.author.username))
    return redirect(url_for(".explore"))


@main.route("/unlike/<int:post_id>", methods=["POST"])
@login_required
def unlike(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        flash("Post not found.")
        return redirect(url_for(".index"))
    if current_user == post.author:
        return redirect(url_for(".index"))
    current_user.unlike(post)
    db.session.commit()
    flash("You unliked a post by {}".format(post.author.username))
    return redirect(url_for(".index"))


@main.route("/like_comment/<int:comment_id>", methods=["POST", "GET"])
@login_required
def like_comment(comment_id):
    if request.method == "GET":
        return redirect(url_for(".index"))
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash("comment not found.")
        return redirect(
            url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    if current_user == comment.author:
        return redirect(
            url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    current_user.like_comment(comment)
    comment.author.add_notification(
        "comment_likes_count", comment.author.new_notifications()
    )  # ADDING LIKED COMMENT NOTIFICATIONS
    db.session.commit()
    flash("You liked a comment by {}".format(comment.author.username))
    return redirect(url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id))


@main.route("/unlike_comment/<int:comment_id>", methods=["POST"])
@login_required
def unlike_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is None:
        flash("Comment not found.")
        return redirect(
            url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    if current_user == comment.author:
        return redirect(
            url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    current_user.unlike_comment(comment)

    db.session.commit()
    flash("You unliked a comment by {}".format(comment.author.username))
    return redirect(url_for(".post_detail", id=comment.post.id) + "#" + str(comment.id))


@main.route("/send_message/<recipient>", methods=["POST", "GET"])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if request.method == "POST":
        if form.validate_on_submit():
            msg = Message(author=current_user, recipient=user, body=form.message.data)
            user.add_notification("unread_message_count", user.new_messages())
            db.session.add(msg)
            db.session.commit()
            flash("Your message has been sent")
            return redirect(url_for("bp.user", username=recipient))
    return render_template(
        "user/send_message.html", title="Send Message", form=form, recipient=recipient
    )


@main.route("/message")
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)

    db.session.commit()

    page = request.args.get("page", 1, type=int)

    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()
    ).paginate(page, current_app.config["POST_PER_PAGE"], False)
    next_url = (
        url_for(".messages", page=messages.next_num) if messages.has_next else None
    )
    prev_url = (
        url_for(".messages", page=messages.prev_num) if messages.has_prev else None
    )
    return render_template(
        "main/messages.html",
        messages=messages.items,
        prev_url=prev_url,
        next_url=next_url,
    )


@main.route("/export_posts")
@login_required
def export_posts():
    if current_user.get_task_in_progress("export_posts"):
        flash("An export task is currently in progress")
    else:
        current_user.launch_task("export_posts", "Exporting posts...")
        db.session.commit()
    return redirect(url_for("bp.user", username=current_user.username))


@main.route("/load_photo/<username>")
def serve_photo(username):
    folder = f"photos/{username}/profile_pictures"
    folder = os.path.abspath(folder)
    filename = os.listdir(folder)[
        0
    ]  # First picture in the list of pictures in the director directory
    return send_from_directory(folder, filename)


@main.route("/users-list/<int:post_id>")
def users_list():
    post_id = request.args.get("post_id")

    post = Post.query.filter_by(id=post_id)

    if post is None:
        return
    users = post.likes
    1
    return jsonify({"users": users})
