from wtforms.validators import (
    ValidationError,
    Length,
    DataRequired,
    Email,
    EqualTo,
    Regexp,
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize, FileRequired
from wtforms import (
    StringField,
    EmailField,
    PasswordField,
    BooleanField,
    SubmitField,
    FileField,
    TextAreaField,
)
from app.models import User
from flask import request
from flask_babel import lazy_gettext as _l


class LoginForm(FlaskForm):
    username = StringField("Username or email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    fullname = StringField("Full Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField(
        "Email", validators=[DataRequired(), Email("Enter a valid email address")]
    )

    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "re-type Password", validators=[DataRequired(), EqualTo("password")]
    )

    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.lower()).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class FileForm(FlaskForm):
    file = FileField(
        "Choose photo",
        validators=[
            DataRequired(),
            FileRequired(),
            FileAllowed(upload_set=["png", "jpeg", "jpg"]),
            FileSize(max_size=5 * 1024 * 1024),
        ],
    )
    submit = SubmitField("Upload")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Request Password Reset")


class SearchForm(FlaskForm):
    q = StringField(label="Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formadata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}

        super(SearchForm, self).__init__(*args, **kwargs)
