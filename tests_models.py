"""Model tests."""

import os
from unittest import TestCase
from decimal import Decimal
from models import db, User, Cart, RecipeCart, Recipe, Ingredient, RecipeIngredient, Category, Conversion


os.environ['DATABASE_URL'] = "postgresql:///recipe-blank"

from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Cart.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no carts
        self.assertEqual(len(u.carts), 0)

    def test_user_signup(self):
        """Test user model signup method"""

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="password123"
        )
        db.session.commit()
        self.assertEqual(user.email, 'test@test.com')
        self.assertEqual(user.username, 'testuser')
        self.assertNotEqual(user.password, 'password123')

    def test_user_serialize(self):
        """Test user model serialize method"""

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="password123"
        )
        db.session.commit()
        self.assertEqual(user.serialize(), 
        {"id":user.id, 
        "username":"testuser", 
        "email":"test@test.com"})
    
    def test_user_authenticate(self):
        """Test user model authenticate method"""

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="password123"
        )
        db.session.commit()
        invalid_username_user = User.authenticate(username='baduser', password='password123')
        self.assertNotEqual(invalid_username_user, user)
        invalid_password_user = User.authenticate(username='testuser', password='password124')
        self.assertNotEqual(invalid_password_user, user)
        valid_user = User.authenticate(username='testuser', password='password123')
        self.assertEqual(valid_user, user)

class RecipeModelTestCase(TestCase):
    """Test model for Recipe"""

    def setUp(self):
        RecipeIngredient.query.delete()
        Ingredient.query.delete()
        Recipe.query.delete()
        Category.query.delete()
        Conversion.query.delete()

        self.client = app.test_client()
    
    def test_recipe_model(self):
        recipe = Recipe(
            title='test_title',
            category='beef',
            prep_time=50,
            difficulty=2,
            spice_level=3
        )
        db.session.add(recipe)
        db.session.commit()

        self.assertEqual(recipe.title, 'test_title')
        self.assertEqual(recipe.category, 'beef')
        self.assertEqual(recipe.prep_time, 50)
        self.assertEqual(recipe.difficulty, 2)
        self.assertEqual(recipe.spice_level, 3)
        self.assertEqual(len(recipe.steps), 0)
        self.assertEqual(len(recipe.contents().all()), 0)

    def test_recipe_serialize(self):
        recipe = Recipe(
            title='test_title',
            category='beef',
            prep_time=50,
            difficulty=2,
            spice_level=3
        )
        db.session.add(recipe)
        db.session.commit()

        self.assertEqual(recipe.serialize(), {"id":recipe.id, 
        "title":"test_title", 
        "category":"beef",
        "prep_time":50,
        "difficulty":2,
        "spice_level":3})

    def test_recipe_contents(self):
        recipe = Recipe(
            title='test_title',
            category='beef',
            prep_time=50,
            difficulty=2,
            spice_level=3
        )

        category = Category(category_label='test_grouping')
        conversion = Conversion(unit_from='unit1', unit_to='unit1', food_type='General', conversion_factor=1)
        db.session.add_all([recipe, category, conversion])
        db.session.commit()
        ingredient = Ingredient(food_name='test_ingredient', 
                                unit='unit1', 
                                category_id = category.id, 
                                conversion_id = conversion.id)
        db.session.add(ingredient)
        db.session.commit()
        db.session.add(RecipeIngredient(recipe_id=recipe.id, 
                                        ingredient_id=ingredient.id, 
                                        quantity=3))
        db.session.commit()

        self.assertEqual(len(recipe.contents().all()), 1)
        self.assertEqual(recipe.contents().all(), [(Decimal(3), ingredient)])

class CartModelTestCase(TestCase):
    """Test model for carts."""

    def setUp(self):

        User.query.delete()
        Cart.query.delete()
        RecipeCart.query.delete()
        Recipe.query.delete()

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()
        self.client = app.test_client()
        self.user_id = u.id

    def test_cart_model(self):
        """Does basic model work?"""

        cart = Cart(
            user_id=self.user_id
        )

        db.session.add(cart)
        db.session.commit()

        # User should have no carts
        self.assertEqual(cart.name, 'Untitled Cart')
        self.assertEqual(cart.is_complete, False)
        self.assertEqual(len(cart.contents().all()), 0)

    def test_cart_contents(self):
        """Test user model signup method"""
        cart = Cart(
            user_id=self.user_id
        )
        db.session.add(cart)
        recipe = Recipe(
            title='test_title',
            category='beef',
            prep_time=50,
            difficulty=2,
            spice_level=3
        )
        db.session.add(recipe)
        db.session.commit()
        db.session.add(RecipeCart(recipe_id=recipe.id, cart_id=cart.id, quantity=2))
        db.session.commit()
        self.assertEqual(len(cart.contents().all()), 1)
        self.assertEqual(cart.contents().all(), [(Decimal(2), recipe)])
    
