from . import bp
from flask import (
    render_template,
    redirect,
    request,
    current_app,
    url_for,
    flash,
)
from flask_login import login_required, current_user
from app.models import Post, User, PusherNotification
from app import db
from .forms import EmptyForm, EditProfileForm, FileForm, SearchForm, PostForm
import os
from werkzeug.utils import secure_filename
from flask import g
from flask_babel import get_locale
import random


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()
        g.empty_form = EmptyForm()
        g.post_form = PostForm()
    g.locale = str(get_locale())


@bp.route("/<username>")
# @login_required
def user(username):
    prev = request.referrer
    g.prev = prev
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found")
        return redirect(url_for("main.index"))
    form = EmptyForm()
    page = request.args.get("page", 1, type=int)

    posts = (
        user.posts.union(user.liked_post)
        .order_by(Post.timestamp.desc())
        .paginate(
            page=page, per_page=current_app.config["POST_PER_PAGE"], error_out=False
        )
    )
    next_url = (
        url_for(".user", username=user.username, page=posts.next_num)
        if posts.has_next
        else None
    )
    prev_url = (
        url_for(".user", username=user.username, page=posts.prev_num)
        if posts.has_prev
        else None
    )

    return render_template(
        "user/user.html",
        user=user,
        posts=posts.items,
        form=form,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved")
        return redirect(url_for(".edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("user/edit_profile.html", title="Edit Profile", form=form)


# @bp.route("/upload_picture/<username>", methods=["GET", "POST"])
# @login_required
# def upload_picture(username):
#     form = FileForm()
#     if form.validate_on_submit():
#         uploaded_file = form.file.data
#         filename = secure_filename(uploaded_file.filename)
#         if filename != "":
#             # img = ProfilePhotos(
#             #     img=uploaded_file.read(),
#             #     mimetype=uploaded_file.mimetype,
#             #     user_id=current_user.id,
#             # )
#             # db.session.add(img)
#             # db.session.commit()
#             if not os.path.exists(f"photos/{username}/profile_pictures"):
#                 os.makedirs(f"photos/{username}/profile_pictures")
#             file_extension = filename.split(".")[1]
#             new_filename = f"{username}_profile_picture"
#             filename = ".".join([new_filename, file_extension])
#             uploaded_file.save(
#                 os.path.join(f"photos/{username}/profile_pictures", filename)
#             )
#             flash("Photo changed", "success")

#             return redirect(url_for("user", username=username))
#     return render_template("user/profile_picture.html", form=form)


@bp.route("/follow/<username>", methods=["POST", "GET"])
@login_required
def follow(username):
    # USE AJAX TO HANDLE THIS LOGIC
    if request.method == "GET":
        return redirect(url_for(".user", username=username))
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for(".user", username=username))
        current_user.follow(user)

        new_notification = PusherNotification(
            action="user_followed", source=current_user, target=user
        )

        db.session.add(new_notification)

        user.add_notification("user_followed", user.new_pusher_notifications())

        db.session.commit()
        flash("You followed {}".format(username))
        return redirect(request.referrer + "#")
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash("User {} not found.".format(username))
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for(".user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You unfollowed {}".format(username))
        return redirect(url_for(".user", username=username))
    else:
        flash("something went wrong")
        return redirect(url_for("main.index"))


@bp.route("/<username>/popup")
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template("user/user_popup.html", user=user, form=form)


@bp.route("/users-recommended")
@login_required
def users_recommended():
    users = User.query.all()
    form = EmptyForm()
    users.remove(current_user)
    for _user in users:
        if current_user.is_following(_user) or _user.is_following(current_user):
            users.remove(_user)
    user = random.choices(users, k=4)
    return render_template("user/user_recommended.html", users=users, form=form)
