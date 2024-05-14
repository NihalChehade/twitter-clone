"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_signup_a_user(self):
        user = User.signup("gfgfg", "test@test.com", "pass", None)
        uid = 1
        user.id = uid
        db.session.add(user)
        db.session.commit()

        u = User.query.get(uid)
        self.assertEqual(u.username, "gfgfg")
        self.assertEqual(u.email, "test@test.com")
        self.assertNotEqual(u.password, "pass")
      

    def test_invalid_username(self):
        user = User.signup(None, "test@test.com", "pass", None)
        user_id = 2
        user.id = user_id
        with self.assertRaises(exc.IntegrityError) as raised:
            db.session.add(user)
            db.session.commit()

    def test_invalid_email(self):
        user = User.signup("rrrr", None, "pass", None)
        user_id = 5555
        user.id = user_id
        with self.assertRaises(exc.IntegrityError) as raised:
            db.session.add(user)
            db.session.commit()
    
    def test_invalid_password(self):
        with self.assertRaises(ValueError) as raised:
            User.signup("tttt", "test@test.com", "", None)

    def test_authentication_of_user(self):
        user = User.signup("nnnn", "test@test.com", "pass", None)
        user_id = 1
        user.id = user_id

        
        db.session.add(user)
        db.session.commit()

        u = User.query.get(user_id)

        u = User.authenticate("nnnn", "pass")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, user_id)

    def test_non_matching_password(self):
        user = User.signup("nnnn", "test@test.com", "pass", None)
        user_id = 1
        user.id = user_id

        
        db.session.add(user)
        db.session.commit()

        self.assertFalse(User.authenticate("nnnn", "fgdsgsdgsdg"))
    
    def test_wrong_username(self):
        user = User.signup("nnnn", "test@test.com", "pass", None)
        user_id = 1
        user.id = user_id

        
        db.session.add(user)
        db.session.commit()

        self.assertFalse(User.authenticate("ssss", "pass"))

    
        
    def test_follow(self):
        user1 = User.signup("nnnn", "test@test.com", "pass", None)
        user1_id = 1
        user1.id = user1_id

        user2 = User.signup("gfgfg", "test1@test.com", "passsss", None)
        user2_id = 2
        user2.id = user2_id
        
        db.session.add(user1)
        db.session.add(user2)
        

        user1.following.append(user2)
        db.session.commit()

        u1 = User.query.get(user1_id)
        u2 = User.query.get(user2_id)

        self.assertEqual(u1.following[0].id, u2.id)
        self.assertEqual(u2.followers[0].id, u1.id)
        self.assertEqual(len(u1.followers), 0)
        self.assertEqual(len(u1.following), 1)
        self.assertEqual(len(u2.following), 0)
        self.assertEqual(len(u2.followers), 1)
        

        

    def test_is_following(self):
        user1 = User.signup("nnnn", "test@test.com", "pass", None)
        user1_id = 1
        user1.id = user1_id

        user2 = User.signup("gfgfg", "test1@test.com", "passsss", None)
        user2_id = 2
        user2.id = user2_id
        
        db.session.add(user1)
        db.session.add(user2)
        

        user1.following.append(user2)
        db.session.commit()

        u1 = User.query.get(user1_id)
        u2 = User.query.get(user2_id)

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

    def test_is_followed(self):
        user1 = User.signup("nnnn", "test@test.com", "pass", None)
        user1_id = 1
        user1.id = user1_id

        user2 = User.signup("gfgfg", "test1@test.com", "passsss", None)
        user2_id = 2
        user2.id = user2_id
        
        db.session.add(user1)
        db.session.add(user2)
        

        user1.following.append(user2)
        db.session.commit()

        u1 = User.query.get(user1_id)
        u2 = User.query.get(user2_id)

        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))