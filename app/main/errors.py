from flask import render_template
from . import main

"""
This module defines the routers of the error pages.
"""

"""Router to the 404 error page"""
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

"""Router to the 500 error page"""
@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

"""Router to the 403 error page"""
@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403