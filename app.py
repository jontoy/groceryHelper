from flask import Flask, request, redirect, render_template, jsonify, flash, session, g, url_for
from models import db, connect_db, Recipe, Ingredient, Category, RecipeIngredient, Step, User, Favorite, Cart, RecipeCart, Conversion
from sqlalchemy import func
from functools import wraps
from forms import CartAddForm, UserAddForm, LoginForm
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from collections import defaultdict
import os

CURR_USER_KEY = "curr_user"
CURR_CART_KEY = "curr_cart"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///recipe'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-secret')
app.config['RECIPES_PER_PAGE'] = 40
app.config['IMAGE_PATH'] = os.environ.get('IMAGE_PATH', 'https://jt-springboard-recipe-bucket.s3-us-west-2.amazonaws.com')

connect_db(app)
db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Access Unauthorized.", "danger")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        user = User.query.filter_by(id=session[CURR_USER_KEY]).first()
        if user:
            g.user = user
        else:
            del session[CURR_USER_KEY]
    else:
        g.user = None
@app.before_request
def add_cart_to_g():
    if CURR_CART_KEY in session:
        cart = Cart.query.filter_by(id=session[CURR_CART_KEY]).first()
        if cart:
            g.cart = cart
        else:
            del session[CURR_CART_KEY]
    else:
        g.cart = None

def create_cart(name=None):
    """
    Creates new Cart object, adds it to DB
    and sets it to g.cart
    """
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

def floatToString(value):
    result = '{0:.2f}'.format(value).rstrip('0').rstrip('.')
    return '0' if result == '-0' else result

@app.context_processor
def utility_processor():
    return dict(floatToString=floatToString,
                image_path=app.config['IMAGE_PATH'])
############################################################################
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')
############################################################################
# Auth Routes
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
        return redirect(url_for('index_recipes'))
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
            return redirect(url_for('index_recipes'))

        flash("Invalid credentials.", 'danger')
    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash('You have been successfully logged out.', 'success')
    return redirect(url_for('home'))

##############################################################################
# Recipe Routes
##############################################################################
@app.route('/recipes')
def index_recipes():
    """
    Show paginated index of recipes in database.
    Recipes can be filtered by protein category, prep time, difficulty,
    spice level and whether favorited by current user.
    """
    recipes_query = Recipe.query
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    if category not in [None, '']:
        recipes_query = recipes_query.filter_by(category=category)
    time = request.args.get('time',60)
    if not time == None:
        recipes_query = recipes_query.filter(Recipe.prep_time <= time)
    difficulty = request.args.get('difficulty')
    if difficulty not in [None, '']:
        recipes_query = recipes_query.filter_by(difficulty=difficulty)
    spice = request.args.get('spice')
    if spice not in [None, '']:
        recipes_query = recipes_query.filter_by(spice_level=spice)

    favorites_only = request.args.get('faves')
    if g.user:
        favorites = [recipe.id for recipe in g.user.favorites]
        if favorites_only:
            recipes_query = recipes_query.filter(Recipe.id.in_(favorites))
    else:
        favorites = []
    recipes_query = recipes_query.order_by(Recipe.id)
    recipes = recipes_query.paginate(page,app.config['RECIPES_PER_PAGE'], False)

    next_url = url_for('index_recipes', 
                        category=category,
                        time=time,
                        difficulty=difficulty,
                        spice=spice,
                        faves=favorites_only,
                        page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('index_recipes', 
                        category=category,
                        time=time,
                        difficulty=difficulty,
                        spice=spice,
                        faves=favorites_only,
                        page=recipes.prev_num) \
        if recipes.has_prev else None
    if g.cart:
        recipes_in_cart = RecipeCart.query.filter(RecipeCart.cart_id == g.cart.id).all()
        recipes_in_cart = [entry.recipe_id for entry in recipes_in_cart]
    else:
        recipes_in_cart = []

    return render_template('recipes/index.html', 
                            recipes=recipes.items,
                            recipes_in_cart=recipes_in_cart,
                            favorites=favorites, 
                            category=category, 
                            difficulty=difficulty, 
                            spice=spice, 
                            time=time,
                            faves=favorites_only,
                            page=page,
                            next_url=next_url,
                            prev_url=prev_url)

@app.route('/recipes/<int:recipe_id>')
def show_recipe(recipe_id):
    """
    Show detailed information on recipe.
    Includes recipe ingredients and directions not seen
    in recipe index thumbnail.
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    ingredients = recipe.contents().all()
    ingredients = [(floatToString(qty), ingr.unit.lower(), ingr.food_name.lower()) for qty, ingr in ingredients]
    return render_template('recipes/show.html', recipe=recipe, steps=steps, ingredients=ingredients)

@app.route('/api/recipes/<int:recipe_id>/add-to-cart', methods=['POST'])
def add_to_cart(recipe_id):
    """
    API route to add a recipe to the current user cart.
    Will return an error if user is not logged in.
    """
    if not g.user:
        return jsonify({"message": "Access Unauthorized: You must be logged in."}), 401
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
    return jsonify({"message": f'Recipe {recipe.id} added to cart',
        "data":recipe_cart.serialize()}), 202

@app.route('/api/recipes/<int:recipe_id>/favorite', methods=['POST'])
def favorite_recipe(recipe_id):
    """
    API route to add a recipe to the current user's favorites.
    Will return an error if user is not logged in 
    or recipe already in favorites.
    """
    if not g.user:
        return jsonify({"message": "Access Unauthorized: You must be logged in."}), 401
    recipe = Recipe.query.get_or_404(recipe_id)
    if not recipe in g.user.favorites:
        db.session.add(Favorite(user_id=g.user.id, recipe_id=recipe_id))
        db.session.commit()
        return jsonify({"message": f'Recipe {recipe_id} favorited.',
        "data":recipe.serialize()}), 202
    else:
        return jsonify({"message": f'Recipe {recipe_id} already in favorites.'}), 405

@app.route('/api/recipes/<int:recipe_id>/unfavorite', methods=['POST'])
def unfavorite_recipe(recipe_id):
    """
    API route to remove a recipe to the current user's favorites.
    Will return an error if user is not logged in 
    or recipe not in favorites.
    """
    if not g.user:
        return jsonify({"message": "Access Unauthorized: You must be logged in."}), 401
    favorite = Favorite.query.filter(Favorite.user_id == g.user.id, Favorite.recipe_id == recipe_id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({"message": f'Recipe {recipe_id} unfavorited.'}), 202
    else:
        return jsonify({"message": f'Recipe {recipe_id} not currently in favorites.'}), 405

##################################################################################################
# Cart Routes
##################################################################################################
@app.route('/carts')
@login_required
def index_carts():
    """
    Show index of current user's carts.
    Carts are divided into active (g.cart), 
    completed (historical), and incomplete (saved for later).
    User must be logged in.
    """
    carts_query = Cart.query.filter(Cart.user_id == g.user.id)
    if g.cart:
        carts_query = carts_query.filter(Cart.id != g.cart.id)

        curr_cart_recipes = g.cart.query_contents().all()
    else:
        curr_cart_recipes = []

    complete_carts = [(cart, cart.query_contents().all()) for cart in carts_query.filter(Cart.is_complete == True).all()]
    incomplete_carts = [(cart, cart.query_contents().all()) for cart in carts_query.filter(Cart.is_complete == False).all()]
    return render_template('carts/index.html', complete_carts=complete_carts, incomplete_carts=incomplete_carts, curr_cart_recipes=curr_cart_recipes)

@app.route('/carts/new', methods=['GET', 'POST'])
@login_required
def new_cart():
    """
    Handle new cart logic.
    Create new cart and add to DB. User must be logged in.
    Redirect to cart index.
    If form not valid, present form.
    """
    form = CartAddForm()
    if form.validate_on_submit():
        if len(form.name.data) > 0:
            create_cart(name=form.name.data)
        else:
            create_cart()
        return redirect(url_for('index_carts'))
    return render_template('/carts/new.html', form=form)

@app.route('/carts/<int:cart_id>', methods=['POST'])
@login_required
def edit_cart(cart_id):
    """
    Handle edit cart name logic.
    Modifies specified cart's name and add to DB. 
    User must be logged in. Redirect to cart index.
    """
    cart = Cart.query.get_or_404(cart_id)
    name = request.form.get('name')
    if len(name) > 0:
        cart.name = name
        db.session.add(cart)
        db.session.commit()
        flash(f'Active cart name changed to {cart.name}', 'success')
    else:
        flash('Carts must have a name', 'danger')
    return redirect(url_for('index_carts'))

@app.route('/carts/<int:cart_id>/copy', methods=['POST'])
@login_required
def copy_cart(cart_id):
    """
    Copies content of specified cart.
    Creates a new cart with name "<old_cart_name> (Copy)" and
    sets recipes and associated quantities to match those of the
    old cart.
    The new cart is set to g.cart. User must be logged in.
    Redirects to cart index.
    """
    cart = Cart.query.get_or_404(cart_id)
    recipe_cart = RecipeCart.query.filter(RecipeCart.cart_id == cart_id)
    recipe_qtys = [(item.recipe_id, item.quantity) for item in recipe_cart]
    create_cart(name=f'{cart.name}(copy)')
    for recipe_id, qty in recipe_qtys:
        db.session.add(RecipeCart(recipe_id=recipe_id, quantity=qty, cart_id=g.cart.id))
    db.session.commit()
    flash(f'Cart "{cart.name}" successfully copied.', 'success')
    return redirect(url_for('index_carts'))
    
@app.route('/carts/<int:cart_id>/activate', methods=['POST'])
@login_required
def activate_cart(cart_id):
    """
    Sets g.cart to specified cart.
    Does not work with completed (historical) carts.
    User must be logged in.
    Redirects to index carts
    """
    cart = Cart.query.get_or_404(cart_id)
    if not cart.is_complete:
        make_cart_active(cart)
        flash(f'Cart "{cart.name}" activated!', 'success')
    else:
        flash('A historical cart cannot be activated. Please use the "Pull recipes from cart" functionality', 'danger')
    return redirect(url_for('index_carts'))

@app.route('/carts/<int:cart_id>/delete', methods=['POST'])
@login_required
def delete_cart(cart_id):
    """
    Deletes specified cart from DB.
    Cart's user_id must match current user.
    User must be logged in.
    Redirects to index carts.
    """
    cart = Cart.query.get_or_404(cart_id)
    if cart.user_id == g.user.id:
        cart_name = cart.name
        if g.cart and cart.id == g.cart.id:
            clear_active_cart()
        db.session.delete(cart)
        db.session.commit()
        flash(f'Cart "{cart_name}" deleted.', 'success')
    else:
        flash('Access unauthorized', 'danger')
    return redirect(url_for('index_carts'))


@app.route('/carts/<int:cart_id>/checkout')
@login_required
def checkout(cart_id):
    """
    Aggregates quantities of ingredients for recipes in current cart
    and displays total ingredients required by category and item.
    Cart's user_id must match current user's. User must be logged.
    Moves cart status to completed (historical) upon use.
    """
    cart = Cart.query.get_or_404(cart_id)
    if not cart.user_id == g.user.id:
        flash('Forbidden Resource: Cart does not belong to user.')
        return redirect(url_for('index_carts'))
    totals = cart.query_ingredient_quantities().all()

    ingr_grouped_by_category = defaultdict(list)
    for name,unit,qty,label in totals:
        ingr_grouped_by_category[label].append((name.lower(), unit.lower(), floatToString(qty)))
    
    ingr_by_category = [{'category':k, 'ingredients':v} for k,v in ingr_grouped_by_category.items()]

    cart.is_complete = True;
    db.session.add(cart)
    db.session.commit()

    if g.cart and (cart_id == g.cart.id):
        clear_active_cart()
    
    return render_template('carts/checkout.html', ingr_by_category=ingr_by_category, cart=cart)

@app.route('/carts/recipe/<int:recipe_id>', methods=['POST'])
@login_required
def edit_cart_item(recipe_id):
    """
    Edits quantity of given recipe in current cart.
    User must be logged in and have current cart.
    Redirects to index carts.
    """
    if g.cart:
        recipe_cart = RecipeCart.query.filter(RecipeCart.recipe_id == recipe_id, RecipeCart.cart_id == g.cart.id).first()
        if not recipe_cart:
            flash('Recipe not found is cart', 'danger')
        else:
            quantity = int(request.form.get('quantity'))
            recipe_cart.quantity = quantity
            db.session.add(recipe_cart)
            db.session.commit()
            flash(f'Cart Recipe "{recipe_cart.recipe.title}" updated', 'success')
    else:
        flash('Only recipes of current cart can be altered', 'danger')
    return redirect(url_for('index_carts'))

@app.route('/carts/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_cart_item(recipe_id):
    """
    Deletes recipe from current cart.
    User must be logged in and have current cart.
    Redirects to index carts.
    """
    if g.cart:
        recipe_cart = RecipeCart.query.filter(RecipeCart.recipe_id == recipe_id, RecipeCart.cart_id == g.cart.id).first()
        if not recipe_cart:
            flash('Recipe not found is cart', 'danger')
        else:
            recipe_title = recipe_cart.recipe.title
            db.session.delete(recipe_cart)
            db.session.commit()
            flash(f'Cart Recipe "{recipe_title}" removed.', 'success')
    else:
        flash('Only recipes of current cart can be altered', 'danger')
    return redirect(url_for('index_carts'))


