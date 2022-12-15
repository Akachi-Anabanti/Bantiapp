from wtforms.validators import (
    Length,
    DataRequired,
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize, FileRequired
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
)

from flask import request
from flask_babel import lazy_gettext as _l


class MessageForm(FlaskForm):
    message = TextAreaField(
        label="Message", validators=[DataRequired(), Length(min=0, max=140)]
    )
    submit = SubmitField("Send")


class PostForm(FlaskForm):
    post = TextAreaField(
        "What is on your mind?", validators=[DataRequired(), Length(min=1, max=200)]
    )
    submit = SubmitField("Share")


class CommentForm(FlaskForm):
    comment = TextAreaField("", validators=[DataRequired(), Length(min=1, max=200)])
    submit = SubmitField("comment")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    q = StringField(label="Search", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formadata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}

        super(SearchForm, self).__init__(*args, **kwargs)
