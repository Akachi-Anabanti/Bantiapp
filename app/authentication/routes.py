# app/auth/routes.py
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from app import db
from app.models import User
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email
from datetime import datetime
from . import auth


@auth.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        logout_user()
        
    form = LoginForm()
    if form.validate_on_submit():
        if len(form.username.data.split("@")) == 2:
            user = User.query.filter_by(email=form.username.data.lower()).first()
        else:
            user = User.query.filter_by(username=form.username.data.lower()).first()
            
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password", category="error")
            return redirect(url_for(".login"))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.index")
        return redirect(next_page)
        
    return render_template("auth/login.html", title="Sign In", form=form)

@auth.route("/logout")
def logout():
    logout_user()
    flash("You logged out", category="info")
    return redirect(url_for(".login"))

@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.lower(),
            email=form.email.data.lower(),
            full_name=form.fullname.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        try:
            db.session.commit()
            flash("Registration successful", category="message")
            return redirect(url_for("main.index"))
        except:
            flash("Something went wrong try again", category="error")
            
    return render_template("auth/register.html", title="Register", form=form)

@auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            "Check your email for the instructions to reset your password",
            category="info",
        )
        return redirect(url_for(".login"))
        
    return render_template(
        "auth/reset_password_request.html",
        title="Reset Password",
        form=form
    )

@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
        
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("main.index"))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.", category="info")
        return redirect(url_for(".login"))
        
    return render_template("auth/reset_password.html", form=form)