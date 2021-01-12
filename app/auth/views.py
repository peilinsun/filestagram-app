from flask import render_template, redirect, url_for, flash, request
from . import auth
from .forms import LoginForm, RegisterationForm, changePasswordForm
from ..models import User
from flask_login import login_user, logout_user, login_required, current_user
from .. import db
# from ..email import send_email

"""
This module defines the routers of the authentication pages in Filestagram.
"""

"""Check if the current user is authenficated before the request.
"""
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

"""Router to the login page
"""
@auth.route("/login", methods=["GET", "POST"])
def login():
    loginError = None
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get("next") or url_for("main.index"))
        loginError = "Invalid email or password"
    return render_template("auth/login.html", form=form, loginError=loginError)

"""Router to logout, and redirect to the login page
"""
@auth.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("You has been logged out.")
    return redirect(url_for("auth.login"))

"""Router to the new user registration page
"""
@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegisterationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, password=form.password.data,
                    username=form.username.data)
        db.session.add(user)
        db.session.commit()
        # token = user.generate_confirmation_token()
        # send_email(user.email, "Confirm Your Account", "auth/email/confirm",user=user,token=token)
        flash("You have registered successfully")
        # return redirect(url_for("auth.login"))

        login_user(user, False)
        return redirect(url_for("main.index"))
    return render_template("auth/register.html", form=form)

"""Router to the password changing page
"""
@auth.route("/changePassword", methods=["GET", "POST"])
@login_required
def change_password():
    form = changePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.password.data
        db.session.add(current_user)
        flash("Change password successfully")
        return redirect(url_for("main.index"))
    return render_template("auth/changePassword.html", form=form)

