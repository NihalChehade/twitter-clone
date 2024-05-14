"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from models import db, User, Message, Likes
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
""" create the tables in our warbler-test database"""
db.create_all()


class UserModelTestCase(TestCase):
    """Test Message Model"""

    def setUp(self):
        """Before every test function signup a user! and create a test client"""
        db.drop_all()
        db.create_all()

        
        user = User.signup("test_username", "test_email@test.com", "test_password", None)
        self.user_id =1
        user.id = self.user_id
        db.session.add(user)
        db.session.commit()

        self.u = User.query.get(self.user_id)

        self.client = app.test_client()

    def tearDown(self):
        """After every test function rollback to delete any insertions in our db"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """test adding a new message """
        
        m = Message(
            text="test_message",
            user_id=self.user_id
        )

        db.session.add(m)
        db.session.commit()

        # User should have 1 message
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "test_message")

    def test_message_likes(self):
        """ test liking a message"""
        message1 = Message(
            text="test_message1",
            user_id=self.uid
        )

        message2 = Message(
            text="test_message2",
            user_id=self.user_id 
        )

        user2 = User.signup("test_username2", "testemail2@email.com", "testPassword2", None)
        
        user2.id = 2
        db.session.add_all([message1, message2, user2])
        db.session.commit()

        user2.likes.append(message1)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == 2).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message1.id)


        