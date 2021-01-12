from flask_login import UserMixin
from hashlib import md5
from . import db
from datetime import datetime
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import login_manager

from werkzeug.security import generate_password_hash, check_password_hash

"""
This module contains the RDS tables class that specifies the tables 
in the database used to store user authentication information and following 
operations.
"""

class Role(db.Model):
    __tablename__="roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self):
        return "<Role %r>"%self.name

    @staticmethod
    def insert_roles():
        roles = {
            "User" : (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
            "Moderator" : (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS, False ),
            "Administrator" : (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class Follow(db.Model):
    """
    This class inferits from the db object.
    Used to store operations of following.

    Each record will have an follower_id, and the user id the follower followed.

    'Followed_id' and 'follower_id' are both user ids. 
    """
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    """
    This class inferits from the db object and UserMixin in flask_user.
    Used to store the user information.

    Each user will have an unique id, username, email, location, about_me, 
    member_since time, last_seen time, hashed password, profile image, role.

    'Followed' and 'followers' indicate its relationship with the Follow table
    """

    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64),unique=True, index=True)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)
    password_hash = db.Column(db.String(128))
    image_filename = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(2047), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        """
        Initialize the table, create default roles, set profile image
        """
        super(User, self).__init__(**kwargs)
        Role.insert_roles()
        if self.role is None:
            if self.email == current_app.config["FLASKY_ADMIN"]:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        # self.image_url =  photos.url("user/default.png")
        self.image_url = self.avatar(128)

    def avatar(self, size):
        """
        Creates and returns a default avatar image for users.

        size: size of the avatar image
        """
        digest = md5(str(self.email).encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @property
    def followed_posts(self):
        # TODO
        return []

    @password.setter
    def password(self,password):
        """Generate hased password

        password: the original password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        """Check hased password

        password: the original password
        """
        return check_password_hash(self.password_hash, password)

    def confirm(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("confirm") != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def ping(self):
        """Update the last time the current user logged in.
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @staticmethod
    def confirm_token_user(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None
        id = data.get("reset")
        if id:
            return User.query.get(int(id))
        return None

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return False

    def follow(self, user):
        """Follow another user and update the table.

        user: An user object
        """
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        """Unfollow another user and update the table.

        user: An user object
        """
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        """Check if the current user is following another user.

        user: An user object
        """
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        """Check if the current user is followed by another user.

        user: An user object
        """
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    def __repr__(self):
        return "<User> %r"%self.username


class Permission:
    FOLLOW = 0x02
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80



