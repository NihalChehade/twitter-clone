"""test user views"""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase
from bs4 import BeautifulSoup
from models import db, Message, User, Likes, Follows


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """test views for users"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.user1 = User.signup("test1", "test1@test.com","testpass1",None)
        self.user1_id = 1111
        self.user1.id = self.user1_id

        self.user2 = User.signup("test2", "test2@test.com", "testpass2", None)
        self.user2_id = 2222
        self.user2.id = self.user2_id

        self.user3 = User.signup("test3", "test3@test.com", "testpass3", None)
        self.user3_id = 3333
        self.user3.id = self.user3_id

        self.user4 = User.signup("abcd", "test4@test.com", "testpass4", None)
        self.user5 = User.signup("efgh", "test5@test.com", "testpass5", None)

        db.session.add_all([self.user1, self.user2, self.user3, self.user4, self.user5])

        db.session.commit()


    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp
    
    def test_users(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertIn("@abcd", str(resp.data))
            self.assertIn("@efgh", str(resp.data))


    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
             


    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@test1", str(resp.data))
            self.assertIn("@test2", str(resp.data))    
            self.assertIn("@test3", str(resp.data))        

            self.assertNotIn("@abcd", str(resp.data))
            self.assertNotIn("@efgh", str(resp.data))
    

    def setup_likes(self):
        msg1 = Message(text="gssggdgd", user_id=self.user1_id)
        msg2 = Message(text="rrrrrrrr", user_id=self.user1_id)
        msg3 = Message(id=6666, text="bbbbbbbbbb", user_id=self.user2_id)
        db.session.add_all([msg1, msg2, msg3])
        db.session.commit()

        like1 = Likes(user_id=self.user1_id, message_id=6666)

        db.session.add(like1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            
            self.assertEqual(len(found), 4)
            self.assertIn("2", found[0].text)
            self.assertIn("0", found[1].text)
            self.assertIn("0", found[2].text)
            self.assertIn("1", found[3].text)

    def test_add_like(self):
        msg = Message(id=5555, text="hhhhhhhhhhhhhhh", user_id=self.user2_id)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.post("/messages/5555/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==5555).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.user1_id)

    def test_remove_like(self):
        self.setup_likes()

        msg = Message.query.filter(Message.text=="bbbbbbbbbb").one()
        self.assertIsNotNone(msg)
        self.assertNotEqual(msg.user_id, self.user1_id)

        l = Likes.query.filter(
            Likes.user_id==self.user1_id and Likes.message_id==msg.id
        ).one()

       
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.post(f"/messages/{msg.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==msg.id).all()
           
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="bbbbbbbbbb").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.user2_id, user_following_id=self.user1_id)
        f2 = Follows(user_being_followed_id=self.user3_id, user_following_id=self.user1_id)
        f3 = Follows(user_being_followed_id=self.user1_id, user_following_id=self.user2_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_user_show_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.user1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test1", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)

    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.get(f"/users/{self.user1_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test2", str(resp.data))
            self.assertIn("@test3", str(resp.data))
            self.assertNotIn("@abcd", str(resp.data))
            self.assertNotIn("@efgh", str(resp.data))

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1_id

            resp = c.get(f"/users/{self.user1_id}/followers")

            self.assertIn("@test2", str(resp.data))
            self.assertNotIn("@test3", str(resp.data))
            self.assertNotIn("@abcd", str(resp.data))
            self.assertNotIn("@efgh", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.user1_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.user1_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    

