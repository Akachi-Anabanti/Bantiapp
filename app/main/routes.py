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
from app.notifications import (notify_comment, notify_comment_like, notify_follow,
                           notify_message, notify_new_post, notify_post_like)

from flask_login import login_required, current_user
from app.models.comment import Comment
from app.models.post import Post
from app.models.notification import Notification
from app.models.user import User
from app.models.message import Message
from app.models.notification import PusherNotification
from app import db
from .forms import PostForm, CommentForm, MessageForm, SearchForm, EmptyForm
from datetime import datetime
from flask import abort


@main.before_app_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()
        g.empty_form = EmptyForm()
        g.post_form = PostForm()


@main.route("/explore")
@login_required
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
        flash("Your post is live!", category="message")
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


@main.route("/post/<string:_id>", methods=["GET", "POST"])
@login_required
def post_detail(_id):
    post = Post.query.filter_by(pid=_id).first_or_404()
    form = CommentForm()
    prev = request.referrer
    g.prev = prev
    comments = post.comments
    if request.method == "POST":
        modalbody = request.form.get("post-comment")
        if form.validate_on_submit():
            comment_body = form.comment.data
            new_comment = Comment(
                body=comment_body,
                author_id=current_user.id,
                post_id=post.id,
            )
            db.session.add(new_comment)
            new_comment.post = post
            db.session.commit()
        elif modalbody and modalbody.strip():
            comment_body = request.form.get("post-comment")
            new_comment = Comment(
                body=comment_body,
                author_id=current_user.id,
                post_id=post.id,
            )
            db.session.add(new_comment)
            new_comment.post = post
            db.session.commit()
        else:
            return redirect(url_for(".post_detail", _id=_id) + "#")
        return redirect(url_for(".post_detail", _id=_id) + "#" + str(new_comment.cid))
    return render_template(
        "main/post.html",
        form=form,
        comments=comments,
        post=post,
    )


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
            post = Post.query.get(post_id)
            reply.post = post
            reply.comment = Comment.query.get(parent_id)
            db.session.commit()
            return redirect(
                url_for(".post_detail", _id=post.pid) + "#" + str(reply.cid)
            )
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
    size = request.args.get("s")
    if size and size == "l":
        return render_template(
            "main/large_search.html",
            posts=posts,
            prev_url=prev_url,
            next_url=next_url,
        )
    else:
        return render_template(
            "main/search.html",
            title="Search",
            posts=posts,
            prev_url=prev_url,
            next_url=next_url,
        )


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


@main.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like(post_id):
    if request.method == "GET":
        return redirect(url_for(".index"))
    post = Post.query.get(post_id)
    # if post is None:
    #     flash("post not found.", category="error")
    #     return redirect(url_for(".index"))
    if current_user == post.author:
        return redirect(url_for(".index"))
    current_user.like_post(post)
    new_notification = PusherNotification(
        action="post_liked", source_id=current_user.id, target_id=post.author.id
    )
    db.session.add(new_notification)

    post.author.add_notification("post_liked", post.author.new_pusher_notifications())
    db.session.commit()
    # current_app.pusher('blog', 'post_liked',)
    flash("You liked a post by {}".format(post.author.username), category="info")
    return redirect(request.referrer)


@main.route("/unlike/<int:post_id>", methods=["POST"])
@login_required
def unlike(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if current_user == post.author:
        return redirect(url_for(".index"))
    current_user.unlike_post(post)
    db.session.commit()
    flash("You unliked a post by {}".format(post.author.username), category="info")
    return redirect(request.referrer)


@main.route("/like_comment/<int:comment_id>", methods=["POST"])
@login_required
def like_comment(comment_id):

    comment = Comment.query.get(comment_id)

    if comment is None or current_user == comment.author:
        return redirect(url_for(".index"))

    current_user.like_comment(comment)

    new_notification = PusherNotification(
        action="comment_liked", source_id=current_user.id, target_id=comment.author.id
    )
    db.session.add(new_notification)

    comment.author.add_notification(
        "post_liked", comment.author.new_pusher_notifications()
    )
    db.session.commit()

    flash("You liked a comment by {}".format(comment.author.username), category="info")

    return redirect(url_for(".post_detail", _id=comment.post.pid) + "#")


@main.route("/unlike_comment/<int:comment_id>", methods=["POST"])
@login_required
def unlike_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first_or_404()
    if current_user == comment.author:
        return redirect(url_for(".post_detail", _id=comment.post.id) + "#")
    current_user.unlike_comment(comment)
    db.session.commit()
    flash(
        "You unliked a comment by {}".format(comment.author.username), category="info"
    )
    return redirect(url_for(".post_detail", _id=comment.post.pid) + "#")


@main.route("/send_message/<recipient>", methods=["POST", "GET"])
@login_required
def send_message(recipient):
    if current_user.username == recipient:
        return redirect(url_for("bp.user", username=recipient))
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if request.method == "POST":
        if form.validate_on_submit():
            msg = Message(author=current_user, recipient=user, body=form.message.data)
            user.add_notification("unread_message_count", user.new_messages())
            db.session.add(msg)
            db.session.commit()
            flash("Your message has been sent", category="message")
            return redirect(url_for(".chat", username=recipient))
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

    messages = current_user.messages_received.union(current_user.messages_sent.filter(Message.sender_id==current_user.id)).order_by(
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
        title="Messages",
        messages=messages.items,
        prev_url=prev_url,
        next_url=next_url,
    )


@main.route("/chat/<username>", methods=["POST", "GET"])
@login_required
def chat(username):

    form = MessageForm()

    user = User.query.filter_by(username=username).first_or_404()

    if not current_user.is_following(user):
        flash("You have to follow this user to be able to chat with them!", "warning")
        return redirect(request.referrer)
    page = request.args.get("page", 1, type=int)

    received_messages = current_user.messages_sent.filter(
        Message.recipient_id == user.id
    )

    sent_messages = current_user.messages_received.filter(Message.sender_id == user.id)

    messages = received_messages.union(sent_messages).order_by(Message.timestamp.asc())
    return render_template(
        "main/chat.html",
        title="Chat",
        form=form,
        messages=messages,
        user=user,
    )


@main.route("/export_posts")
@login_required
def export_posts():
    if current_user.get_task_in_progress("export_posts"):
        flash("An export task is currently in progress", category="warning")
    else:
        current_user.launch_task("export_posts", "Exporting posts...")
        db.session.commit()
    return redirect(url_for("bp.user", username=current_user.username))


@main.route("/notification_list")
@login_required
def notification_list():
    current_user.last_notification_checked_time = datetime.utcnow()
    current_user.add_notification("post_liked", 0)
    current_user.add_notification("user_followed", 0)

    db.session.commit()

    page = request.args.get("page", 1, type=int)

    notification = current_user.pusher_notifications_received.order_by(
        PusherNotification.timestamp.desc()
    ).paginate(page, current_app.config["POST_PER_PAGE"], False)
    next_url = (
        url_for(".notification_list", page=notification.next_num)
        if notification.has_next
        else None
    )
    prev_url = (
        url_for(".notification_list", page=notification.prev_num)
        if notification.has_prev
        else None
    )
    if request.args.get("s", type=str) == "l":
        return render_template(
            "main/large_notification.html",
            notifications=notification.items,
            prev_url=prev_url,
            next_url=next_url,
        )
    else:
        return render_template(
            "main/notification.html",
            notifications=notification.items,
            prev_url=prev_url,
            next_url=next_url,
        )


@main.route("/<username>/followers")
@login_required
def userfollowers(username):
    form = EmptyForm()
    user = User.query.filter_by(username=username).first_or_404()

    users = user.followed.union(user.followers)
    return render_template(
        "user/followers_list.html",
        title=f"{username}/follows",
        users=users,
        form=form,
    )


@main.route("/activities")
def activities():
    return render_template("main/activities.html")
