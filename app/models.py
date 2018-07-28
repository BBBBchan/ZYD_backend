from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    permission = db.Column(db.Integer)


followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=True)
    avatarUrl = db.Column(db.String(100), nullable=True)
    openid = db.Column(db.String(50), unique=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref='users')

    tag = db.Column(db.String(30))
    pricing = db.Column(db.Numeric(precision=2))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user) and user != self:
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user) and user != self:
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_works(self, cls):
        return cls.query.join(followers, (followers.c.followed_id == cls.author_id)).filter(
            followers.c.follower_id == self.id).order_by(cls.upload_time.desc())

    def is_designer(self):
        return self.role_id == 2

    def is_admin(self):
        return self.role_id == 3


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    description = db.Column(db.Text)


class StarVideo(db.Model):
    __tablename__ = 'star_video'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='video_stars')

    content_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    content = db.relationship('Video', backref='stars')


class StarPicture(db.Model):
    __tablename__ = 'star_picture'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='picture_stars')

    content_id = db.Column(db.Integer, db.ForeignKey('picture.id'))
    content = db.relationship('Picture', backref='stars')


class CommentVideo(db.Model):
    __tablename__ = 'comment_video'

    id = db.Column(db.Integer, primary_key=True)

    observer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    observer = db.relationship('User')

    context = db.Column(db.Text)

    content_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    content = db.relationship('Video', backref='comments')

    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    parent_id = db.Column(db.Integer, db.ForeignKey('comment_video.id'), default=None)
    parent = db.relationship('CommentVideo', uselist=False)


class CommentPicture(db.Model):
    __tablename__ = 'comment_picture'

    id = db.Column(db.Integer, primary_key=True)

    observer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    observer = db.relationship('User')

    context = db.Column(db.Text)

    content_id = db.Column(db.Integer, db.ForeignKey('picture.id'))
    content = db.relationship('Picture', backref='comments')

    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    parent_id = db.Column(db.Integer, db.ForeignKey('comment_picture.id'), default=None)
    parent = db.relationship('CommentPicture', uselist=False)


class Picture(db.Model):
    __tablename__ = 'picture'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(100))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    showcase_id = db.Column(db.Integer, db.ForeignKey('showcase.id'))

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='pictures')

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='pictures')


class Video(db.Model):
    __tablename__ = 'video'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(100))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='videos')

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='videos')


class ShowCase(db.Model):
    __tablename__ = 'showcase'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    description = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='showcases')

    pictures = db.relationship('Picture', backref='showcase', lazy='dynamic')


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50))
    customer = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller = db.Column(db.Integer, db.ForeignKey('user.id'))
    all_price = db.Column(db.Numeric(precision=2))
    status = db.Column(db.Integer)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
