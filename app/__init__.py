from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_s3 import FlaskS3
import flask_s3

from config import config
from flask_uploads import (UploadSet, configure_uploads, ALL, IMAGES, 
                           UploadNotAllowed, patch_request_class, UploadConfiguration)
from .utils.utils import CustomizeUploadSet
from .utils.aws_utils import AWS_session
from .dymodels import create_all as dynamo_create_all



aws_worker_session = AWS_session('root')

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
pagedown = PageDown()

photos = CustomizeUploadSet('photos', IMAGES)
uploaded_files = CustomizeUploadSet('files', ALL)

# if set to "strong", remeber me will not work
login_manager.session_protection = "basic"
login_manager.login_view = "auth.login"

s3 = FlaskS3()

from .models import  User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    #dynamo_delete_all()
    dynamo_create_all()
    login_manager.init_app(app)
    pagedown.init_app(app)
    configure_uploads(app, photos)
    configure_uploads(app, uploaded_files)
    patch_request_class(app)
    
    with app.app_context():
        db.create_all()
    return app


app = create_app("production")


