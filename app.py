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
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = 'my-secret'
app.config['RECIPES_PER_PAGE'] = 40

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

def floatToString(value):
    result = '{0:.2f}'.format(value).rstrip('0').rstrip('.')
    return '0' if result == '-0' else result


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
    recipes = recipes_query.paginate(page,app.config['RECIPES_PER_PAGE'], False)
    next_url = url_for('index_recipes', 
                        category=category,
                        time=time,
                        difficulty=difficulty,
                        spice=spice,
                        page=recipes.next_num) \
        if recipes.has_next else None
    prev_url = url_for('index_recipes', 
                        category=category,
                        time=time,
                        difficulty=difficulty,
                        spice=spice,
                        page=recipes.prev_num) \
        if recipes.has_prev else None

    recipes_in_cart = RecipeCart.query.filter(RecipeCart.cart_id == g.cart.id).all()
    recipes_in_cart = [entry.recipe_id for entry in recipes_in_cart]
    return render_template('recipes/index.html', 
                            recipes=recipes.items,
                            recipes_in_cart=recipes_in_cart, 
                            category=category, 
                            difficulty=difficulty, 
                            spice=spice, 
                            time=time,
                            page=page,
                            next_url=next_url,
                            prev_url=prev_url)
    

@app.route('/recipes/<int:recipe_id>')
def show_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    steps = Step.query.filter_by(recipe_id=recipe_id).order_by(Step.step_number).all()
    ingredients = db.session \
                    .query(RecipeIngredient.quantity, Ingredient.unit, Ingredient.food_name) \
                    .join(Ingredient) \
                    .filter(RecipeIngredient.recipe_id == recipe_id) \
                    .order_by(func.lower(Ingredient.food_name)) \
                    .all()
    ingredients = [(floatToString(qty), unit, name) for qty, unit, name in ingredients]
    return render_template('recipes/show.html', recipe=recipe, steps=steps, ingredients=ingredients)

##################################################################################################
@app.route('/carts')
def index_carts():
    carts_query = Cart.query.filter(Cart.user_id == g.user.id)
    if g.cart:
        carts_query = carts_query.filter(Cart.id != g.cart.id)

        curr_cart_recipes = g.cart.contents().all()
    else:
        curr_cart_recipes = []

    complete_carts = [(cart, cart.contents().all()) for cart in carts_query.filter(Cart.is_complete == True).all()]
    incomplete_carts = [(cart, cart.contents().all()) for cart in carts_query.filter(Cart.is_complete == False).all()]
    return render_template('carts/index.html', complete_carts=complete_carts, incomplete_carts=incomplete_carts, curr_cart_recipes=curr_cart_recipes)

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
@app.route('/carts/<int:cart_id>/copy', methods=['POST'])
def copy_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    recipe_cart = RecipeCart.query.filter(RecipeCart.cart_id == cart_id)
    recipe_qtys = [(item.recipe_id, item.quantity) for item in recipe_cart]
    create_cart(name=f'{cart.name}(copy)')
    for recipe_id, qty in recipe_qtys:
        db.session.add(RecipeCart(recipe_id=recipe_id, quantity=qty, cart_id=g.cart.id))
    db.session.commit()
    flash(f'Cart {cart.name} successfully copied.', 'success')
    return redirect(url_for('index_carts'))
    
@app.route('/carts/<int:cart_id>/activate', methods=['POST'])
def activate_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    if not cart.is_complete:
        make_cart_active(cart)
        flash(f'Cart {cart.name} activated!', 'success')
    else:
        flash('A historical cart cannot be activated. Please use the "Pull recipes from cart" functionality', 'danger')
    return redirect(url_for('index_carts'))

@app.route('/carts/<int:cart_id>/delete', methods=['POST'])
def delete_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    if cart.user_id == g.user.id:
        if cart.id == g.cart.id:
            clear_active_cart()
        db.session.delete(cart)
        db.session.commit()
        flash('Cart deleted.', 'success')
    else:
        flash('Access unauthorized', 'danger')
    return redirect(url_for('index_carts'))

@app.route('/carts/<int:cart_id>/checkout')
def checkout(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    totals = db.session.query(Ingredient.food_name, Ingredient.unit, func.sum(RecipeIngredient.quantity*RecipeCart.quantity), Category.category_label) \
               .select_from(RecipeCart) \
               .join(RecipeIngredient, RecipeCart.recipe_id == RecipeIngredient.recipe_id) \
               .join(Ingredient, RecipeIngredient.ingredient_id == Ingredient.id) \
               .join(Category, Ingredient.category_id == Category.id) \
               .filter(RecipeCart.cart_id == cart.id) \
               .group_by(Ingredient.food_name, Ingredient.unit, Category.category_label) \
               .order_by(Category.category_label, func.lower(Ingredient.food_name)).all()

    ingr_grouped_by_category = defaultdict(list)
    for name,unit,qty,label in totals:
        ingr_grouped_by_category[label].append((name, unit, floatToString(qty)))
    
    ingr_by_category = [{'category':k, 'ingredients':v} for k,v in ingr_grouped_by_category.items()]

    cart.is_complete = True;
    db.session.add(cart)
    db.session.commit()

    if g.cart and (cart_id == g.cart.id):
        clear_active_cart()
    
    return render_template('carts/checkout.html', ingr_by_category=ingr_by_category)

@app.route('/carts/recipe/<int:recipe_id>/edit', methods=['POST'])
def edit_cart_item(recipe_id):
    recipe_cart = RecipeCart.query.filter(RecipeCart.recipe_id == recipe_id, RecipeCart.cart_id == g.cart.id).first()
    if not recipe_cart:
        flash('Recipe not found is cart')
    else:
        quantity = int(request.form.get('quantity'))
        recipe_cart.quantity = quantity
        db.session.add(recipe_cart)
        db.session.commit()
        flash(f'Cart Recipe "{recipe_cart.recipe.title}" Updated', 'success')
    return redirect('/carts')

@app.route('/carts/recipe/<int:recipe_id>/delete', methods=['POST'])
def delete_cart_item(recipe_id):
    recipe_cart = RecipeCart.query.filter(RecipeCart.recipe_id == recipe_id, RecipeCart.cart_id == g.cart.id).first()
    if not recipe_cart:
        flash('Recipe not found is cart')
    else:
        db.session.delete(recipe_cart)
        db.session.commit()
    return redirect('/carts')

@app.route('/api/recipes/<int:recipe_id>/add-to-cart', methods=['POST'])
def add_to_cart_ajax(recipe_id):
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
        "data":recipe_cart.serialize()})
