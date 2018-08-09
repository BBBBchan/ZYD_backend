from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from app.models import *
from app import app


manager = Manager()
manager.add_command('server', Server())

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


def create_roles():
    """
    创建角色表
    shell里运行create_roles创建角色
    """
    roles = {
        'User': Permission.NAME_MODIFY | Permission.AVATAR_MODIFY | Permission.COMMENT | Permission.SHARE |
        Permission.REPORT | Permission.ORDER_SUBMIT | Permission.FOLLOW | Permission.DESIGNER_APPLY |
        Permission.WORK_MANAGE | Permission.SHOWCASE_MANAGE,
        'Designer': Permission.NAME_MODIFY | Permission.AVATAR_MODIFY | Permission.COMMENT | Permission.SHARE |
        Permission.REPORT | Permission.ORDER_SUBMIT | Permission.FOLLOW | Permission.DESIGNER_APPLY |
        Permission.WORK_MANAGE | Permission.SHOWCASE_MANAGE | Permission.ORDER_RECEIVED_WRITE | Permission.ORDER_DEAL |
        Permission.BILLBOARD_WORK_CONFIRM | Permission.SUPER_DESIGNER_APPLY,
        'SuperDesigner': Permission.NAME_MODIFY | Permission.AVATAR_MODIFY | Permission.COMMENT | Permission.SHARE |
        Permission.REPORT | Permission.ORDER_SUBMIT | Permission.FOLLOW | Permission.DESIGNER_APPLY |
        Permission.WORK_MANAGE | Permission.SHOWCASE_MANAGE | Permission.ORDER_RECEIVED_WRITE | Permission.ORDER_DEAL |
        Permission.BILLBOARD_WORK_CONFIRM,
        'Admin': Permission.NAME_MODIFY | Permission.AVATAR_MODIFY | Permission.COMMENT | Permission.SHARE |
        Permission.REPORT | Permission.ORDER_SUBMIT | Permission.FOLLOW | Permission.DESIGNER_APPLY |
        Permission.WORK_MANAGE | Permission.SHOWCASE_MANAGE | Permission.ORDER_RECEIVED_WRITE | Permission.ORDER_DEAL |
        Permission.BILLBOARD_WORK_CONFIRM | Permission.SUPER_DESIGNER_APPLY | Permission.ADMIN,
        'Banned': Permission.BANNED
    }
    for r in roles:
        role = Role.query.filter_by(name=r).first()
        if role is None:
            role = Role(name=r)
            role.permission = roles[r]
            db.session.add(role)
    db.session.commit()


@manager.shell
def make_shell_context():
    return dict(app=app, db=db, role=Role, user=User, category=Category, picture=Picture, video=Video, order=Order,
                star_video=StarVideo, star_picture=StarPicture, showcase=ShowCase,
                comment_video=CommentVideo, comment_picture=CommentPicture, create_roles=create_roles)


if __name__ == '__main__':
    manager.run()
