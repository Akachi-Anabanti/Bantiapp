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
from app.models import Post, User
from app import db
from .forms import EmptyForm, EditProfileForm, FileForm, SearchForm
import os
from werkzeug.utils import secure_filename
from flask import g
from flask_babel import get_locale


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route("/<username>")
# @login_required
def user(username):
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


@bp.route("/upload_picture/<username>", methods=["GET", "POST"])
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
    return render_template("user/profile_picture.html", form=form)


@bp.route("/follow/<username>", methods=["POST", "GET"])
@login_required
def follow(username):
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
        db.session.commit()
        flash("You followed {}".format(username))
        return redirect(url_for(".user", username=username))
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
        return redirect(url_for("main.index"))
