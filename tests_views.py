"""Views tests."""

import os
from unittest import TestCase
from decimal import Decimal

os.environ['DATABASE_URL'] = "postgresql:///recipe-test"


from app import app, CURR_USER_KEY, CURR_CART_KEY


app.config['WTF_CSRF_ENABLED'] = False


class RecipesViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

    #     self.testuser = User.signup(username="testuser",
    #                                 email="test@test.com",
    #                                 password="test",
    #                                 image_url=None)
    #     self.u1 = User.signup(username="apple_girl", email='apple@test.com', password='test', image_url=None)
    #     self.u2 = User.signup(username="bagel_man", email='bagel@test.com', password='test', image_url=None)
    #     self.u3 = User.signup(username="carrot_girl", email='carrot@test.com', password='test', image_url=None)
    #     self.u4 = User(id=44444, username="danish_man", email='danish@test.com', password='test', image_url=None)
    #     db.session.add(self.u4)
    #     self.u5 = User(id=55555, username="eggplant_man", email='eggplant@test.com', password='test', image_url=None)
    #     db.session.add(self.u5)
    #     db.session.commit()

    def test_index_recipes(self):

        with self.client as c:


            resp = c.get('/recipes')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Shumai Meatballs', html)
            self.assertIn('Roasted Eggplant Salad', html)
            self.assertIn('Brown Butter Shrimp', html)
            self.assertIn('Classic Chicken Piccata', html)
            self.assertNotIn('No recipes found.', html)

    def test_search_recipes(self):
        with self.client as c:

            resp = c.get('/recipes?difficulty=2&spice=0')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertNotIn('Roasted Eggplant Salad', html)
            self.assertIn('Shumai Meatballs', html)
            self.assertNotIn('Brown Butter Shrimp', html)
            self.assertIn('Classic Chicken Piccata', html)
            self.assertNotIn('No recipes found.', html)

    def test_search_recipes_no_results(self):
        with self.client as c:
            resp = c.get('/recipes?difficulty=1&spice=3&time=10')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('No recipes found.', html)

    def test_add_to_cart_no_user(self):
        with self.client as c:
            resp = c.post('/api/recipes/1/add-to-cart')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 401)
            self.assertIn("Access Unauthorized", html)

    def test_index_carts_no_user(self):
        with self.client as c:
            resp = c.get("/carts", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_new_carts_no_user(self):
        with self.client as c:
            resp = c.get("/carts/new", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)
    def test_copy_carts_no_user(self):
        with self.client as c:
            resp = c.post("/carts/2/copy", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)
    def test_activate_carts_no_user(self):
        with self.client as c:
            resp = c.post("/carts/2/activate", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)
    def test_delete_carts_no_user(self):
        with self.client as c:
            resp = c.post("/carts/2/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_checkout_no_user(self):
        with self.client as c:
            resp = c.get("/carts/2/checkout", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    # def test_user_show(self):
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id
    #         resp = c.get(f'/users/{self.testuser.id}')

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('@testuser', html)
    #         self.assertRegex(html, '<a class=\"messages-display-user\".*0</a>')
    #         self.assertRegex(html, '<a class=\"following-display\".*0</a>')
    #         self.assertRegex(html, '<a class=\"follower-display\".*0</a>')
    #         self.assertRegex(html, '<a class=\"likes-display\".*0</a>')

    # def test_user_show_no_user(self):
    #     with self.client as c:
    #         resp = c.get(f'/users/{self.testuser.id}', follow_redirects=True)

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('Access unauthorized', html)
    # def setup_likes(self):
    #     m1 = Message(text="test message", user_id=self.testuser.id)
    #     m2 = Message(text="other thing", user_id=self.testuser.id)
    #     m3 = Message(id=9876, text="liked warble", user_id=self.u1.id)
    #     db.session.add_all([m1, m2, m3])
    #     db.session.commit()

    #     l1 = Likes(user_id=self.testuser.id, message_id=9876)

    #     db.session.add(l1)
    #     db.session.commit()

    # def test_user_show_messages_display(self):
    #     self.setup_likes()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id
            
    #         resp = c.get(f'/users/{self.testuser.id}')

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('@testuser', html)
    #         self.assertRegex(html, '<a class=\"messages-display-user\".*2</a>')
    # def test_user_show_likes_display(self):
    #     self.setup_likes()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id
            
    #         resp = c.get(f'/users/{self.testuser.id}')

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('@testuser', html)
    #         self.assertRegex(html, '<a class=\"likes-display\".*1</a>')

    # def test_add_like(self):
    #     m = Message(id=1984, text="The earth is round", user_id=self.u1.id)
    #     db.session.add(m)
    #     db.session.commit()

    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.post("/messages/1984/like", follow_redirects=True)
    #         self.assertEqual(resp.status_code, 200)

    #         likes = Likes.query.filter(Likes.message_id==1984).all()
    #         self.assertEqual(len(likes), 1)
    #         self.assertEqual(likes[0].user_id, self.testuser.id)

    # def test_add_like_no_user(self):
    #     self.setup_likes()
    #     with self.client as c:
    #         resp = c.post("/messages/9876/like", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn("Access unauthorized", html)

    # def test_remove_like(self):
    #     self.setup_likes()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.post("/messages/9876/unlike", follow_redirects=True)
    #         self.assertEqual(resp.status_code, 200)

    #         likes = Likes.query.filter(Likes.message_id==9876).all()
    #         self.assertEqual(len(likes), 0)

    # def test_remove_like_no_user(self):
    #     self.setup_likes()
    #     with self.client as c:

    #         resp = c.post("/messages/9876/unlike", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn("Access unauthorized", html)

    # def setup_followers(self):
    #     f1 = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u1.id)
    #     f2 = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u2.id)
    #     f3 = Follows(user_being_followed_id=self.u4.id, user_following_id=self.testuser.id)
        
    #     db.session.add_all([f1,f2,f3])
    #     db.session.commit()

    # def test_user_show_following_display(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.get(f'/users/{self.testuser.id}')

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('@testuser', html)
    #         self.assertRegex(html, '<a class=\"following-display\".*1</a>')

    # def test_user_show_followers_display(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.get(f'/users/{self.testuser.id}')

    #         self.assertEqual(resp.status_code, 200)
    #         html = resp.get_data(as_text=True)
    #         self.assertIn('@testuser', html)
    #         self.assertRegex(html, '<a class=\"follower-display\".*2</a>')

    # def test_add_follow(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.post("/users/55555/follow", follow_redirects=True)
    #         self.assertEqual(resp.status_code, 200)

    #         follows = Follows.query.filter(Follows.user_being_followed_id==55555).all()
    #         self.assertEqual(len(follows), 1)

    # def test_add_follow_no_user(self):
    #     self.setup_followers()
    #     with self.client as c:

    #         resp = c.post("/users/55555/follow", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn("Access unauthorized", html)

    # def test_add_follow_invalid_user(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id
    #         resp = c.post("/users/99999999/follow", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 404)
    #         self.assertIn("Page not found", html)

    # def test_remove_follow(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id

    #         resp = c.post("/users/44444/unfollow", follow_redirects=True)
    #         self.assertEqual(resp.status_code, 200)

    #         follows = Follows.query.filter(Follows.user_being_followed_id==44444).all()
    #         self.assertEqual(len(follows), 0)

    # def test_remove_follow_no_user(self):
    #     self.setup_followers()
    #     with self.client as c:

    #         resp = c.post("/users/44444/unfollow", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn("Access unauthorized", html)

    # def test_remove_follow_invalid_user(self):
    #     self.setup_followers()
    #     with self.client as c:
    #         with c.session_transaction() as sess:
    #             sess[CURR_USER_KEY] = self.testuser.id
    #         resp = c.post("/users/999999999/unfollow", follow_redirects=True)
    #         html = resp.get_data(as_text=True)
    #         self.assertEqual(resp.status_code, 404)
    #         self.assertIn("Page not found", html)