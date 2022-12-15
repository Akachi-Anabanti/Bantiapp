from wtforms.validators import (
    ValidationError,
    Length,
    DataRequired,
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, FileField
from app.models import User
from flask import request
from flask_babel import lazy_gettext as _l


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


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


class SearchForm(FlaskForm):
    q = StringField(label="Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formadata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}

        super(SearchForm, self).__init__(*args, **kwargs)
