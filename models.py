from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()
def connect_db(app):
    db.app = app
    db.init_app(app)


class RecipeIngredient(db.Model):
    __tablename__ = "recipes_ingredients"
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    quantity = db.Column(db.Numeric, nullable = False)

class Recipe(db.Model):

    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    title = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text)
    prep_time = db.Column(db.Integer, nullable=True)
    difficulty = db.Column(db.Integer, nullable=True)
    spice_level = db.Column(db.Integer, nullable=True)
    image = db.Column(db.Text)
    steps = db.relationship('Step', backref='recipe', passive_deletes=True)
    
    def serialize(self):
        return {"id":self.id, 
        "title":self.title, 
        "category":self.category,
        "prep_time":self.prep_time,
        "difficulty":self.difficulty,
        "spice_level":self.spice_level}

class Ingredient(db.Model):

    __tablename__ = 'ingredients'
    __table_args__ = (
        db.UniqueConstraint('food_name', 'unit', name='unique_name_unit'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name = db.Column(db.Text, nullable=False)
    unit = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    recipes = db.relationship('Recipe', secondary="recipes_ingredients", backref='ingredients')

    def serialize(self):
        return {"id":self.id, 
        "food_name":self.food_name, 
        "unit":self.unit,
        "category_id":self.category_id}

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    category_label = db.Column(db.Text, nullable=False)

class Step(db.Model):
    __tablename__ = 'steps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    carts = db.relationship('Cart', passive_deletes=True)

    def serialize(self):
        return {"id":self.id, 
        "username":self.username, 
        "email":self.email}

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.
        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, default='Untitled Cart')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    is_complete = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User')
    def contents(self):
        return db.session \
                .query(RecipeCart.quantity, Recipe) \
                .join(Recipe) \
                .filter(RecipeCart.cart_id == self.id) \
                .order_by(Recipe.title)
    def serialize(self):
        return {"id":self.id, "name":self.name, "user_id": self.user_id}

class RecipeCart(db.Model):
    __tablename__ = 'recipes_carts'
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    quantity = db.Column(db.Numeric, nullable = False)
    recipe = db.relationship('Recipe')
    cart = db.relationship('Cart')
    def serialize(self):
        return {"recipe_id":self.recipe_id, "cart_id":self.cart_id, "quantity":str(self.quantity)}