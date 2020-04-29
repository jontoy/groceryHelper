"""Views tests."""

import os
from unittest import TestCase
from decimal import Decimal

os.environ['DATABASE_URL'] = "postgresql:///recipe-test"


from app import app, CURR_USER_KEY, CURR_CART_KEY
from models import User, Cart, RecipeCart, db


app.config['WTF_CSRF_ENABLED'] = False


class RecipesViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        self.testuser = User.query.get(777)
        self.delete_carts_by_user(self.testuser.id)

    def test_index_recipes(self):
        """
        Test index recipes route displays recipes in DB
        """
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
        """
        Test index recipes route filters properly using query parameters
        """
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
        """
        Test index recipes route displays correct message if
        no recipes are found under a filter.
        """
        with self.client as c:
            resp = c.get('/recipes?difficulty=1&spice=3&time=10')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('No recipes found.', html)

    def test_add_to_cart_no_user(self):
        """
        Test add to cart route requires active user.
        """
        with self.client as c:
            resp = c.post('/api/recipes/1/add-to-cart')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 401)
            self.assertIn("Access Unauthorized", html)

    def test_add_to_cart(self):
        """
        Test add to cart route adds correct recipe to cart.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/api/recipes/1/add-to-cart')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 202)
            self.assertIn("Recipe 1 added to cart", html)
    def delete_carts_by_user(self, user_id):
        """
        Utility function for deleting all carts associated with user
        """
        carts = Cart.query.filter_by(user_id = user_id).all()
        for cart in carts:
            db.session.delete(cart)
        db.session.commit()
    def test_index_carts_no_user(self):
        """
        Test index carts route requires active user.
        """
        with self.client as c:
            resp = c.get("/carts", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_index_carts_empty(self):
        """
        Test index carts route displays correct message
        when user has no carts.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get("/carts", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No Active Cart", html)
            self.assertIn("No Carts Saved for Later", html)
            self.assertIn("No Cart History for User", html)

    def test_new_carts_no_user(self):
        """
        Test new cart route requires active user.
        """
        with self.client as c:
            resp = c.get("/carts/new", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)
    def test_copy_carts_no_user(self):
        """
        Test copy cart route requires active user.
        """
        with self.client as c:
            resp = c.post("/carts/2/copy", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_copy_carts(self):
        """
        Test copy cart route creates new cart with correct name
        and makes it the active cart.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            cart = Cart(name='test_cart', user_id=self.testuser.id, is_complete=True)
            db.session.add(cart)
            db.session.commit()
            resp = c.get("/carts", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No Active Cart", html)
            self.assertIn("No Carts Saved for Later", html)
            self.assertNotIn("No Cart History for User", html)

            resp = c.post(f"/carts/{cart.id}/copy", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("No Active Cart", html)
            self.assertIn("test_cart(copy)", html)
            self.assertIn("No Carts Saved for Later", html)
            self.assertNotIn("No Cart History for User", html)

    def test_activate_carts_no_user(self):
        """
        Test activate cart route requires active user.
        """
        with self.client as c:
            resp = c.post("/carts/2/activate", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)
    def test_activate_carts(self):
        """
        Test activate cart route moves correct cart from inactive
        to active cart.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            cart = Cart(name='test_cart', user_id=self.testuser.id)
            db.session.add(cart)
            db.session.commit()

            resp = c.get("/carts", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No Active Cart", html)
            self.assertNotIn("No Carts Saved for Later", html)
            self.assertIn("No Cart History for User", html)

            resp = c.post(f"/carts/{cart.id}/activate", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("No Active Cart", html)
            self.assertIn("No Carts Saved for Later", html)
            self.assertIn("No Cart History for User", html)
    
    def test_delete_carts_no_user(self):
        """
        Test delete cart route requires active user.
        """
        with self.client as c:
            resp = c.post("/carts/2/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_delete_carts(self):
        """
        Test delete cart route removes correct cart from DB.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            cart = Cart(name='test_cart', user_id = self.testuser.id)
            db.session.add(cart)
            db.session.commit()
            resp = c.post(f"/carts/{cart.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'Cart &#34;test_cart&#34; deleted.', html)
            self.assertEqual(len(Cart.query.filter_by(name='test_cart').all()), 0)

    def test_checkout_no_user(self):
        """
        Test checkout route requires active user.
        """
        with self.client as c:
            resp = c.get("/carts/2/checkout", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access Unauthorized", html)

    def test_checkout(self):
        """
        Test checkout aggregation route operates correctly.
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            cart = Cart(name='test_cart', user_id = self.testuser.id)
            db.session.add(cart)
            db.session.commit()
            # Add recipe with 13oz chicken breast
            db.session.add(RecipeCart(recipe_id=4, cart_id=cart.id, quantity=1))
            # Add recipe with 2 whole chicken breast (1 whole = 6.5ox)
            db.session.add(RecipeCart(recipe_id=24, cart_id=cart.id, quantity=2))
            db.session.commit()
            resp = c.get(f"/carts/{cart.id}/checkout", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('39 ounce chicken breast', html)
