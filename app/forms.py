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
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Submit")

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()

            if user is not None:
                raise ValidationError(f"Username '{self.username.data}' has been taken")


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


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class PostForm(FlaskForm):
    post = TextAreaField(
        "What is on your mind?", validators=[DataRequired(), Length(min=1, max=200)]
    )
    submit = SubmitField("Share")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Request Password Reset")


class CommentForm(FlaskForm):
    comment = TextAreaField("", validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField("comment")


class SearchForm(FlaskForm):
    q = StringField(label="Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formadata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}

        super(SearchForm, self).__init__(*args, **kwargs)


class MessageForm(FlaskForm):
    message = TextAreaField(
        label="Message", validators=[DataRequired(), Length(min=0, max=140)]
    )
    submit = SubmitField("Send")
