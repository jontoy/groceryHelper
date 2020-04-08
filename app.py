from flask import Flask, request, redirect, render_template, jsonify, flash, session, g, url_for
from models import db, connect_db, Recipe, Ingredient, Category, RecipeIngredient, Step, User, Cart, RecipeCart
from sqlalchemy import func
from forms import CartAddForm, UserAddForm, LoginForm
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from collections import defaultdict

CURR_USER_KEY = "curr_user"
CURR_CART_KEY = "curr_cart"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///recipe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'my-secret'

connect_db(app)
db.create_all()

@app.before_request
def add_user_to_g():

    if CURR_USER_KEY in session:
        g.user = User.query.get_or_404(session[CURR_USER_KEY])
    else:
        g.user = None
@app.before_request
def add_user_to_g():

    if CURR_CART_KEY in session:
        g.cart = Cart.query.get_or_404(session[CURR_CART_KEY])
    else:
        g.cart = None

def create_cart(name=None):
    new_cart = Cart(name=name, user_id=g.user.id)
    db.session.add(new_cart)
    db.session.commit()
    session[CURR_CART_KEY] = new_cart.id
    g.cart = new_cart

def make_cart_active(cart):
    session[CURR_CART_KEY] = cart.id

def clear_active_cart():
    if CURR_CART_KEY in session:
        del session[CURR_CART_KEY]

def do_login(user):
    session[CURR_USER_KEY] = user.id

def do_logout():

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    clear_active_cart()



@app.route('/')
def home():
    return render_template('home.html')

############################################################################
@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)
        do_login(user)
        return redirect(url_for('home'))
    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect(url_for('home'))

        flash("Invalid credentials.", 'danger')
    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash('You have been successfully logged out.')
    return redirect(url_for('login'))

##############################################################################


@app.route('/recipes')
def index_recipes():
    # SWAP TO AJAX INSTEAD?
    recipes_query = Recipe.query
    category = request.args.get('category')
    if category and category != '':
        recipes_query = recipes_query.filter_by(category=category)
    max_time = request.args.get('max-time')
    if max_time:
        recipes_query = recipes_query.filter(Recipe.prep_time <= max_time)
    difficulty = request.args.get('difficulty')
    if difficulty:
        recipes_query = recipes_query.filter_by(difficulty=difficulty)
    spice_level = request.args.get('spice-level')
    if spice_level:
        recipes_query = recipes_query.filter_by(spice_level=spice_level)
    recipes = recipes_query.limit(50).all()

    return render_template('recipes/index.html', 
                            recipes=recipes, 
                            category=category, 
                            difficulty=difficulty, 
                            spice_level=spice_level, 
                            max_time=max_time)

@app.route('/recipes/<int:recipe_id>')
def show_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    ingredients = db.session \
                    .query(RecipeIngredient.quantity, Ingredient.unit, Ingredient.food_name) \
                    .join(Ingredient) \
                    .filter(RecipeIngredient.recipe_id == recipe_id) \
                    .all()
    return render_template('recipes/show.html', recipe=recipe, steps=steps, ingredients=ingredients)

@app.route('/recipes/<int:recipe_id>/add-to-cart', methods=['POST'])
def add_to_cart(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if not g.cart:
        create_cart()
    recipe_cart = RecipeCart.query.filter(RecipeCart.recipe_id == recipe_id, RecipeCart.cart_id == g.cart.id).first()
    if recipe_cart:
        recipe_cart.quantity = recipe_cart.quantity + 1
    else:
        recipe_cart = RecipeCart(recipe_id=recipe_id, cart_id=g.cart.id, quantity=1)
    db.session.add(recipe_cart)
    db.session.commit()
    flash(f'Recipe {recipe.id} added to cart')
    return redirect(url_for('index_recipes'))

@app.route('/carts')
def index_carts():
    if g.cart:
        curr_cart_recipes = db.session \
                        .query(RecipeCart.quantity, Recipe) \
                        .join(Recipe) \
                        .filter(RecipeCart.cart_id == g.cart.id) \
                        .all()
    else:
        curr_cart_recipes = []
    carts = Cart.query.filter(Cart.user_id == g.user.id).all()
    return render_template('carts/index.html', carts=carts, curr_cart_recipes=curr_cart_recipes)

@app.route('/carts/new', methods=['GET', 'POST'])
def new_cart():
    form = CartAddForm()
    if form.validate_on_submit():
        if len(form.name.data) > 0:
            create_cart(name=form.name.data)
        else:
            create_cart()
        return redirect('/carts')
    return render_template('/carts/new.html', form=form)

@app.route('/carts/<int:cart_id>/activate', methods=['POST'])
def activate_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    make_cart_active(cart)
    return redirect(url_for('index_carts'))

@app.route('/carts/<int:cart_id>/delete', methods=['POST'])
def delete_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    if cart.user_id == g.user.id:
        if cart.id == g.cart.id:
            clear_active_cart()
        db.session.delete(cart)
        db.session.commit()
    return redirect(url_for('index_carts'))


@app.route('/checkout')
def checkout():
    totals = db.session.query(Ingredient.food_name, Ingredient.unit, func.sum(RecipeIngredient.quantity*RecipeCart.quantity), Category.category_label) \
               .select_from(RecipeCart) \
               .join(RecipeIngredient, RecipeCart.recipe_id == RecipeIngredient.recipe_id) \
               .join(Ingredient, RecipeIngredient.ingredient_id == Ingredient.id) \
               .join(Category, Ingredient.category_id == Category.id) \
               .filter(RecipeCart.cart_id == g.cart.id) \
               .group_by(Ingredient.food_name, Ingredient.unit, Category.category_label) \
               .order_by(Category.category_label, func.lower(Ingredient.food_name)).all()

    # totals = db.session.query(Cart, RecipeCart) \
    #         .select_from('carts') \
    #         .join(RecipeCart) \
    #         .filter(Cart.id == g.cart.id).all()

    res = defaultdict(list)
    for name,unit,qty,label in totals:
        res[label].append((name, unit, qty))
    print(res)
    # for k,v in res.items:
    #     print(k,v)
    
    
    return ''