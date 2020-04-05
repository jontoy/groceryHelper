from flask_sqlalchemy import SQLAlchemy

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
    prep_time = db.Column(db.Integer, nullable=True)
    difficulty = db.Column(db.Integer, nullable=True)
    spice_level = db.Column(db.Integer, nullable=True)
    steps = db.relationship('Step', backref='recipe', lazy=True, passive_deletes=True)

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
