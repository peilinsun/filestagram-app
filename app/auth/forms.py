from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp, EqualTo
from ..models import User
from wtforms import ValidationError
from flask_login import current_user

class LoginForm(FlaskForm):
    """
    FlaskForm for login
    """
    email = StringField("Email", validators=[DataRequired(),Email(),Length(1,64)],render_kw = {"placeholder": "Email"})
    password = PasswordField("Password", validators=[DataRequired()],render_kw = {"placeholder": "Password"})
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign in")

class RegisterationForm(FlaskForm):
    """
    FlaskForm for new user registration, including validation functions of emails and usernames. 
    """
    email = StringField("Email", validators=[DataRequired(),Email(), Length(1,64)])
    username = StringField("Username", validators=[DataRequired(), Length(1,64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                          'Usernames must have only letters,numbers, dots or underscores')])
    password = PasswordField("Password", validators=[DataRequired(),EqualTo("password2","Passwords must match")])
    password2 = PasswordField("Comfirm password", validators=[DataRequired(),EqualTo("password","Passwords must match")])
    submit = SubmitField("Sign up")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is not None:
            raise ValidationError("Email is already registered")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first() is not None:
            raise ValidationError("Username already in use")


class changePasswordForm(FlaskForm):
    """
    FlaskForm for changing the password, including validation functions of the original password and new password. 
    """
    originalPassword = PasswordField("Original Password", validators=[DataRequired()])
    password = PasswordField("New Password", validators=[DataRequired(),EqualTo("password2","Passwords must match")])
    password2 = PasswordField("Comfirm Password", validators=[DataRequired(),EqualTo("password","Passwords must match")])
    submit = SubmitField("Change Password")

    def validate_originalPassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError("Original password is wrong")

    def validate_password(self, field):
        if field.data == self.originalPassword.data:
            raise ValidationError("New password should not be the same with original password!")

