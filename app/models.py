from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Permission:
    """
    使用十六进制表示权限
    普通用户User:              0x03ff
    设计师Designer:            0x3fff
    特约设计师SuperDesigner:    0x1fff
    管理员Admin:                0x7fff
    封禁用户Banned:              0x0000
    """
    NAME_MODIFY = 0x0001  # 修改昵称
    AVATAR_MODIFY = 0x0002  # 修改头像
    COMMENT = 0x0004  # 评论
    SHARE = 0x0008  # 分享
    REPORT = 0x0010  # 举报
    ORDER_SUBMIT = 0x0020  # 发起订单
    FOLLOW = 0x0040  # 关注他人
    DESIGNER_APPLY = 0x0080  # 申请成为设计师
    WORK_MANAGE = 0x0100  # 上传，修改，删除自己的作品
    SHOWCASE_MANAGE = 0x0200  # 建立，修改，删除自己的作品集
    ORDER_RECEIVED_WRITE = 0x0400  # 填写接单信息
    ORDER_DEAL = 0x0800  # 接受、拒绝普通用户的订单申请
    BILLBOARD_WORK_CONFIRM = 0x1000  # 申请、拒绝自己作品上热榜
    SUPER_DESIGNER_APPLY = 0x2000  # 申请成为特约设计师
    ADMIN = 0x4000  # 管理员
    BANNED = 0x0000  # 封禁用户


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    permission = db.Column(db.Integer)

    def __str__(self):
        return self.name


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
    is_banned = db.Column(db.Boolean, default=False)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref='users')

    tag = db.Column(db.String(30))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship('User', secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    pictures = db.relationship('Picture', backref='author', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            # 如果用户角色为空，默认设置用户角色为普通用户
            self.role = Role.query.filter_by(permission=0x03ff).first()

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_works(self, cls):
        """
        按时间倒序获取当前用户关注的用户所发布的作品
        """
        return cls.query.join(followers, (followers.c.followed_id == cls.author_id)).filter(
            followers.c.follower_id == self.id).order_by(cls.upload_time.desc())

    def is_designer(self):
        return self.role_id == 2

    def is_super_designer(self):
        return self.role_id == 3

    def is_admin(self):
        return self.role_id == 4

    def can(self, permission):
        """
        判断用户是否具有某项权限
        """
        return self.role is None and (self.role.permission & permission) == permission

    def __str__(self):
        return self.name


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    description = db.Column(db.Text)
    category = db.relationship('Picture', backref='category', lazy='dynamic')

# 标签表
class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True,index=True)
    name = db.Column(db.String(64))
    tag = db.relationship('Picture', backref='tag',lazy='dynamic')

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

    commentator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    commentator = db.relationship('User')

    context = db.Column(db.Text)

    content_id = db.Column(db.Integer, db.ForeignKey('video.id'))
    content = db.relationship('Video', backref='comments')

    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    parent_id = db.Column(db.Integer, db.ForeignKey('comment_video.id'), default=None)
    parent = db.relationship('CommentVideo', uselist=False)


class CommentPicture(db.Model):
    __tablename__ = 'comment_picture'

    id = db.Column(db.Integer, primary_key=True)

    commentator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    commentator = db.relationship('User')

    context = db.Column(db.Text)

    content_id = db.Column(db.Integer, db.ForeignKey('picture.id'))
    content = db.relationship('Picture', backref='comments')

    created_time = db.Column(db.DateTime, default=datetime.utcnow)


class HotOrder(db.Model):
    """
    热度榜的数据库，方便后台管理
    """
    __tablename__ = 'hot_order'
    id = db.Column(db.Integer,primary_key=True)
    picture_id = db.Column(db.Integer,db.ForeignKey('picture.id'))
    order = db.Column(db.Integer,index=True)


class Picture(db.Model):
    __tablename__ = 'picture'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(100))
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    showcase_id = db.Column(db.Integer, db.ForeignKey('showcase.id'))

    # 类型id
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    # 标签id
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'))

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # 点击量，每一个视频被请求详情时这个数加一
    clicks = db.Column(db.Integer, default = 0)
    # 分享数
    share_count = db.Column(db.Integer,default=0)


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
    # 点击量，每一个视频被请求详情时这个数加一
    clicks = db.Column(db.Integer)


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
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    requirements = db.Column(db.Text)
    all_price = db.Column(db.Numeric(scale=2))
    status = db.Column(db.Integer)  # 0 未完成 1 已完成
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.Integer, default=0)  # 0 未完成 1 已接受 2 已取消
    created_time = db.Column(db.DateTime, default=datetime.utcnow)

    type = db.Column(db.String(30))  # 订单类型 photo / post / design
    time = db.Column(db.DateTime)  # 拍摄时间
    content = db.Column(db.Text)  # 拍摄内容
    thinking = db.Column(db.Text)  # 拍摄思路
    requirements = db.Column(db.Text)  # 需求
    is_take_deposit = db.Column(db.Boolean)  # 是否交定金
    customer_weixin = db.Column(db.String(50))  # 顾客微信号


class TimeText(db.Model):
    Time = db.Column(db.DateTime, primary_key=True)


class ReportMessage(db.Model):
    """
    用户举报消息--主要发往后台
    """
    __tablename__ = 'report_message'
    id = db.Column(db.Integer, primary_key=True)
    # 举报原因
    reason = db.Column(db.String(100))
    # 举报者
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reporter = db.relationship('User', backref='report_messages')
    # 被举报者
    reported_id = db.Column(db.Integer)
    reported = db.relationship('User')
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Boolean, default=False)  # False 未处理， True 已处理


class ApplyMessage(db.Model):
    """
    用户申请消息--主要发往后台
    """
    __tablename__ = 'apply_message'
    id = db.Column(db.Integer, primary_key=True)
    # 申请人
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    applicant = db.relationship('User', backref='apply_messages')
    # 申请类型
    apply_type = db.Column(db.String(30))
    created_time = db.Column(db.DateTime, default=datetime.utcnow)
    # 申请详情
    detail = db.Column(db.Text)
    status = db.Column(db.Boolean, default=False)  # False 未处理， True 已处理



class PushMessage(db.Model):
    """
    向用户推送的消息
    """
    __tablename__ = 'push_message'
    id = db.Column(db.Integer, primary_key=True)
    # 接收者
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver = db.relationship('User', backref='pull_messages')
    content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    """
    系统公告
    """
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.utcnow)


class OrderExtra(db.Model):
    """
    订单详细条目
    """
    __tablename__ = 'order_extra'
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.Boolean)  # 性别
    age = db.Column(db.Integer)  # 年龄
    location = db.Column(db.String(100))  # 拍摄位置
    late_protocol = db.Column(db.String(100))  # 迟到协议
    is_solve_eat = db.Column(db.Boolean)  # 是否解决饮食
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    order = db.relationship('Order', backref='item', uselist=False)

