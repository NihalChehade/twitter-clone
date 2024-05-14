"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 44444
        self.testuser.id = self.testuser_id
        db.session.commit()

    def tearDown(self):
        """After every test function rollback to delete any insertions in our db"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_message_show(self):

        m1 = Message(
            id=656566,
            text="testtttt",
            user_id=self.testuser_id
        )
        
        db.session.add(m1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            m = Message.query.get(656566)

            resp = c.get(f'/messages/{m.id}')
            html = str(resp.data)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p class="single-message">testtttt</p>', html)

    def test_message_delete_authenticated_authorized(self):

        m1 = Message(
            id=656566,
            text="testtttt",
            user_id=self.testuser_id
        )
        
        db.session.add(m1)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/656566/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(656566)
            self.assertIsNone(message)

    def test_not_authorized_message_delete(self):

        # A second user that will try to delete the message
        u = User.signup(username="test2user",
                        email="testuser@test.com",
                        password="pass",
                        image_url=None)
        u.id = 66666

        #Message is owned by testuser
        m = Message(
            id=2222,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = 66666

            resp = c.post("/messages/2222/delete", follow_redirects=True)
            html = str(resp.data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Cannot delete this message!</div>', html)

            m = Message.query.get(2222)
            self.assertIsNotNone(m)

    def test_not_authenticated_message_delete(self):

        message = Message(
            id=2222,
            text="a test message",
            user_id=self.testuser_id
        )
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/2222/delete", follow_redirects=True)
            html = str(resp.data)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

            m = Message.query.get(2222)
            self.assertIsNotNone(m)


    
