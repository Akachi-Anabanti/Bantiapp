from flask_babel import get_locale
from flask import (
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_from_directory,
    jsonify,
)
from flask import g
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse
from app import app, db
from app.forms import (
    LoginForm,
    RegistrationForm,
    EditProfileForm,
    FileForm,
    EmptyForm,
    PostForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
    CommentForm,
    SearchForm,
    MessageForm,
)
from app.models import User, Post, Comment, Message, Notification
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@app.route("/explore")
def explore():
    page = request.args.get("page", 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POST_PER_PAGE"], error_out=False
    )
    next_url = url_for("explore", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("explore", page=posts.prev_num) if posts.has_prev else None
    return render_template(
        "index.html",
        title="Explore",
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/", methods=["POST", "GET"])
@app.route("/index", methods=["POST", "GET"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post is live!")
        return redirect(url_for("index"))
    page = request.args.get("page", 1, type=int)

    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POST_PER_PAGE"], error_out=False
    )
    next_url = url_for("index", page=posts.next_num) if posts.has_next else None
    prev_url = url_for("index", page=posts.prev_num) if posts.has_prev else None

    return render_template(
        "index.html",
        title="Home",
        form=form,
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        if len(form.username.data.split("@")) == 2:
            user = User.query.filter_by(email=form.username.data.lower()).first()
        else:
            user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/user/<username>")
# @login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found")
        return redirect(url_for("index"))
    form = EmptyForm()
    page = request.args.get("page", 1, type=int)

    posts = (
        user.posts.union(user.liked_post)
        .order_by(Post.timestamp.desc())
        .paginate(page=page, per_page=app.config["POST_PER_PAGE"], error_out=False)
    )
    next_url = (
        url_for("user", username=user.username, page=posts.next_num)
        if posts.has_next
        else None
    )
    prev_url = (
        url_for("user", username=user.username, page=posts.prev_num)
        if posts.has_prev
        else None
    )

    return render_template(
        "user.html",
        user=user,
        posts=posts.items,
        form=form,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.route("/upload_picture/<username>", methods=["GET", "POST"])
@login_required
def upload_picture(username):
    form = FileForm()
    if form.validate_on_submit():
        uploaded_file = form.file.data
        filename = secure_filename(uploaded_file.filename)
        if filename != "":
            # img = ProfilePhotos(
            #     img=uploaded_file.read(),
            #     mimetype=uploaded_file.mimetype,
            #     user_id=current_user.id,
            # )
            # db.session.add(img)
            # db.session.commit()
            if not os.path.exists(f"photos/{username}/profile_pictures"):
                os.makedirs(f"photos/{username}/profile_pictures")
            file_extension = filename.split(".")[1]
            new_filename = f"{username}_profile_picture"
            filename = ".".join([new_filename, file_extension])
            uploaded_file.save(
                os.path.join(f"photos/{username}/profile_pictures", filename)
            )
            flash("Photo changed", "success")

            return redirect(url_for("user", username=username))
    return render_template("profile_picture.html", form=form)


@app.route("/load_photo/<username>")
def serve_photo(username):
    folder = f"photos/{username}/profile_pictures"
    folder = os.path.abspath(folder)
    filename = os.listdir(folder)[
        0
    ]  # First picture in the list of pictures in the director directory
    return send_from_directory(folder, filename)


@app.route("/follow/<username>", methods=["POST", "GET"])
@login_required
def follow(username):
    if request.method == "GET":
        return redirect(url_for("user", username=username))
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash("You followed {}".format(username))
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("index"))


@app.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You unfollowed {}".format(username))
        return redirect(url_for("user", username=username))
    else:
        return redirect(url_for("index"))


@app.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():

    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for the instructions to reset your password")

        return redirect(url_for("login"))
    return render_template(
        "reset_password_request.html", title="Rest Password", form=form
    )


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form)


@app.route("/like/<int:post_id>", methods=["POST", "GET"])
@login_required
def like(post_id):
    if request.method == "GET":
        return redirect(url_for("index"))
    post = Post.query.get(post_id)
    if post is None:
        flash("post not found.")
        return redirect(url_for("index"))
    if current_user == post.author:
        return redirect(url_for("index"))
    current_user.like(post)
    db.session.commit()
    flash("You liked a post by {}".format(post.author.username))
    return redirect(url_for("explore"))


@app.route("/unlike/<int:post_id>", methods=["POST"])
@login_required
def unlike(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        flash("Post not found.")
        return redirect(url_for("index"))
    if current_user == post.author:
        return redirect(url_for("index"))
    current_user.unlike(post)
    db.session.commit()
    flash("You unliked a post by {}".format(post.author.username))
    return redirect(url_for("index"))


@app.route("/users-list/<int:post_id>")
def users_list():
    post_id = request.args.get("post_id")

    post = Post.query.filter_by(id=post_id)

    if post is None:
        return
    users = post.likes

    return jsonify({"users": users})


@app.route("/post/<int:id>", methods=["GET", "POST"])
@login_required
def post_detail(id):
    post = Post.query.get(id)
    form = CommentForm()
    if not post:
        flash("Post does not exist")
        return redirect(url_for("index"))
    comments = post.comments
    if request.method == "POST":
        if form.validate_on_submit():

            new_comment = Comment(
                body=form.comment.data,
                author_id=current_user.id,
                post_id=id,
            )
            db.session.add(new_comment)
            new_comment.post = post
            db.session.commit()
            return redirect(url_for("post_detail", id=id) + "#" + str(new_comment.id))
    return render_template("post.html", form=form, comments=comments, post=post)


@app.route("/comment/reply", methods=["GET", "POST"])
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
            return redirect(url_for("post_detail", id=post_id) + "#" + str(reply.id))
    return redirect(url_for("index"))


@app.route("/like_comment/<int:comment_id>", methods=["POST", "GET"])
@login_required
def like_comment(comment_id):
    if request.method == "GET":
        return redirect(url_for("index"))
    comment = Comment.query.get(comment_id)
    if comment is None:
        flash("comment not found.")
        return redirect(
            url_for("post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    if current_user == comment.author:
        return redirect(
            url_for("post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    current_user.like_comment(comment)
    comment.author.add_notification(
        "comment_likes_count", comment.author.new_notifications()
    )  # ADDING LIKED COMMENT NOTIFICATIONS
    db.session.commit()
    flash("You liked a comment by {}".format(comment.author.username))
    return redirect(url_for("post_detail", id=comment.post.id) + "#" + str(comment.id))


@app.route("/unlike_comment/<int:comment_id>", methods=["POST"])
@login_required
def unlike_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is None:
        flash("Comment not found.")
        return redirect(
            url_for("post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    if current_user == comment.author:
        return redirect(
            url_for("post_detail", id=comment.post.id) + "#" + str(comment.id)
        )
    current_user.unlike_comment(comment)

    db.session.commit()
    flash("You unliked a comment by {}".format(comment.author.username))
    return redirect(url_for("post_detail", id=comment.post.id) + "#" + str(comment.id))


@app.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("explore"))

    page = request.args.get("page", 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, app.config["POST_PER_PAGE"])
    next_url = (
        url_for("search", q=g.search_form.q.data, page=page + 1)
        if total > page * app.config["POST_PER_PAGE"]
        else None
    )
    prev_url = (
        url_for("search", q=g.search_form.q.data, page=page - 1) if page > 1 else None
    )
    return render_template(
        "search.html", title="Search", posts=posts, next_url=next_url, prev_url=prev_url
    )


@app.route("/send_message/<recipient>", methods=["POST", "GET"])
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
            return redirect(url_for("user", username=recipient))
    return render_template(
        "send_message.html", title="Send Message", form=form, recipient=recipient
    )


@app.route("/message")
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)

    db.session.commit()

    page = request.args.get("page", 1, type=int)

    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()
    ).paginate(page, app.config["POST_PER_PAGE"], False)
    next_url = (
        url_for("messages", page=messages.next_num) if messages.has_next else None
    )
    prev_url = (
        url_for("messages", page=messages.prev_num) if messages.has_prev else None
    )
    return render_template(
        "messages.html", messages=messages.items, prev_url=prev_url, next_url=next_url
    )


@app.route("/notifications")
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    print(since)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since
    ).order_by(Notification.timestamp.asc())

    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )


# ELASTIC_PASSWORD ="13AI4TYcDeKPu3egelEJ"
# PATH TO HTTP_CA.CERT ="C:\Users\Akachi\Documents\elasticsearch-8.5.2\config\certs\http_ca.crt"
# ELASTICSEARCH CLIENT CONFIG =  client = Elasticsearch("https://localhost:9200", ca_certs="C:/Users/Akachi/Documents/elasticsearch-8.5.2/config/certs/http_ca.crt",basic_auth=("elastic",ELASTIC_PASSWORD))
