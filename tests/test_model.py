from app.models import *
from app import create_app
import unittest


app = create_app('app.config.DevConfig')
print('----------Test start----------')


class TestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_follow(self):
        u1 = User()
        u2 = User()
        u3 = User()
        u4 = User()
        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()
        assert u2.unfollow(u1) is None
        u = u1.follow(u2)
        u1.follow(u3)
        u1.follow(u4)
        assert u == u1
        assert u1.is_following(u2)
        assert u1.followed.count() == 3
        assert u2.followers.count() == 1
        db.session.add(u)
        db.session.commit()
        p2 = Picture(author=u2)
        p3 = Picture(author=u3)
        p4 = Picture(author=u4)
        db.session.add_all([p2, p3, p4])
        db.session.commit()
        assert u1.followed_works(Picture).count() == 3

    def test_comment(self):
        p = Picture()
        c1 = CommentPicture(content=p)
        c2 = CommentPicture(parent=c1, content=p)
        db.session.add_all([p, c1, c2])
        db.session.commit()
        assert c2.parent == c1
        assert c1.content == p and c2.content == p
        assert len(p.comments) == 2, p.comments

    def test_showcase(self):
        p1 = Picture()
        p2 = Picture()
        s = ShowCase()
        s.pictures.append(p1)
        s.pictures.append(p2)
        db.session.add_all([p1, p2, s])
        db.session.commit()
        assert s.pictures.count() == 2

    def test_category(self):
        c1 = Category()
        c2 = Category()
        v1 = Video(category=c1)
        v2 = Video(category=c2)
        v3 = Video(category=c1)
        db.session.add_all([c1, c2, v1, v2, v3])
        db.session.commit()
        assert len(c1.videos) == 2
        assert len(c2.videos) == 1
        assert v1.category == c1

    def test_star(self):
        u1 = User()
        u2 = User()
        v1 = Video()
        s1 = StarVideo(user=u1, content=v1)
        s2 = StarVideo(user=u2, content=v1)
        db.session.add_all([u1, u2, v1, s1, s2])
        db.session.commit()
        assert len(v1.stars) == 2
        assert v1.stars[0] == s1
        assert v1.stars[0].user == u1
        assert v1.stars[0].content == v1


if __name__ == '__main__':
    unittest.main()
