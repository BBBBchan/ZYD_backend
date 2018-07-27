from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand
from app.models import *
from app import app


manager = Manager()
manager.add_command('server', Server())

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.shell
def make_shell_context():
    return dict(app=app, db=db, role=Role, user=User, category=Category, picture=Picture, video=Video, order=Order,
                star_video=StarVideo, star_picture=StarPicture, showcase=ShowCase,
                comment_video=CommentVideo, comment_picture=CommentPicture)


if __name__ == '__main__':
    manager.run()