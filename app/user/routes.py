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
from .forms import EmptyForm, EditProfileForm
from flask import g
import random


@bp.route("/<username>", methods=["GET"])
@login_required
def user(username):
    prev = request.referrer
    g.prev = prev
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    page = request.args.get("page", 1, type=int)

    posts = (
        user.posts.union(user.liked_posts)
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
        flash("Your changes have been saved", category="message")
        return redirect(url_for(".edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("user/edit_profile.html", title="Edit Profile", form=form)


@bp.route("/follow/<username>", methods=["POST", "GET"])
@login_required
def follow(username):
    # USE AJAX TO HANDLE THIS LOGIC
    if request.method == "GET":
        return redirect(url_for(".user", username=username))
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        if user == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for(".user", username=username))
        current_user.follow(user)

        new_notification = PusherNotification(
            action="user_followed", source_id=current_user.id, target_id=user.id
        )

        db.session.add(new_notification)

        user.add_notification("user_followed", user.new_pusher_notifications())

        db.session.commit()
        flash("You followed {}".format(username), category="info")
        return redirect(request.referrer + "#")
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
        if user == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for(".user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash("You unfollowed {}".format(username), category="info")
        return redirect(url_for(".user", username=username))
    else:
        flash("something went wrong", category="error")
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
    if users != []:
        users = random.choices(users)
    else:
        users = []
    return render_template("user/user_recommended.html", users=users, form=form)
