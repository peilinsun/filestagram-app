from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import FileField, StringField, SubmitField, TextAreaField, BooleanField, SelectField
from flask_wtf.file import FileRequired, FileAllowed
from wtforms.validators import DataRequired, Email, Length, Regexp, ValidationError
from ..models import User
from .. import uploaded_files, photos

"""
Main forms of Filestagram
"""

class FilterForm(FlaskForm):
    query = StringField(validators=[DataRequired(), Length(1, 255)])
    submit = SubmitField("Search")

class PostForm(FlaskForm):
    """
    FlaskForm for uploading images, including a file field that only accepts images, 
    and a title that decribes the image.
    """
    file = FileField(validators=[FileAllowed(photos, 'Images only!'),
                                  FileRequired('File was empty!')])
    body = PageDownField(validators=[DataRequired()],render_kw = {"placeholder":"Leave your thought"})
    submit = SubmitField("Submit")


class PostFormFile(FlaskForm):
    """
    FlaskForm for uploading general files, including a file field that accepts all 
    types of files.
    """
    file = FileField(validators=[FileAllowed(uploaded_files, 'Certain types only!'),
                                 FileRequired('File was empty!')])
    submit = SubmitField("Upload files")


class CommentForm(FlaskForm):
    """
    FlaskForm for commenting on users' posts, including a field that supports markdown.
    """
    body = PageDownField(validators=[DataRequired()],render_kw = {"placeholder":"Leave your comment"})
    submit = SubmitField("Comment")


class NameForm(FlaskForm):
    """
    FlaskForm for user names.
    """
    name = StringField("What's your name?",validators=[DataRequired(), Email()],render_kw = {"placeholder": "Enter User Name"})
    submit = SubmitField("Submit")


class EditProfileForm(FlaskForm):
    """
    FlaskForm for editing user profiles, including a file field of user's profile image, 
    location, and personal introduction.
    """
    photo = FileField(validators=[FileAllowed(photos, "Only image supported")])
    location = StringField("Location", render_kw = {"placeholder": "Location"})
    about_me = TextAreaField("About me", render_kw = {"placeholder": "Introduce yourself"})
    submit = SubmitField("Save Changes")
