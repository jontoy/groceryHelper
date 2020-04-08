from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from bs4 import BeautifulSoup
from secrets import EDEMAM_APP_ID, EDEMAM_APP_KEY, USDA_API_KEY
from models import db, connect_db, Recipe, Ingredient, Category, RecipeIngredient, Step
import requests
import time
import re
import os
import json
from decimal import Decimal
import hashlib
from PIL import Image

test_app = Flask('test_app')
test_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///recipe'
test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
test_app.config['SQLALCHEMY_ECHO'] = True

connect_db(test_app)
db.create_all()

def persist_image(folder_path:str,url:str):
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        import io
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_name = hashlib.sha1(image_content).hexdigest()[:10]
        file_path = os.path.join(folder_path, file_name + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=85)
        print(f"SUCCESS - saved {url} - as {file_path}")
        return file_name
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")
        return None

class RecipeParser():
    def __init__(self, homeChefUrl=None, category=None):
        if homeChefUrl:
            self.set_url(homeChefUrl, category)
    def set_url(self, homeChefUrl, category=None):
        res = requests.get(homeChefUrl)
        self.soup = BeautifulSoup(res.text, features='html.parser')
        self.category = category
    def parseRecipe(self):
        self._extract_difficulty()
        self._extract_ingredients()
        self._extract_spice()
        self._extract_steps()
        self._extract_title()
        self._extract_total_time()
    
    def commit_parsed_data(self):
        self._commit_recipe()
        self._commit_steps()
        self._commit_categories()
        self._commit_ingredients()
    def _extract_difficulty(self):
        difficulty_div = self.soup.find(class_='meal__overview').find_all('div')[2].find(class_='meal__indicator')
        difficulty = [class_name.replace('meal__indicator--', '') for class_name in difficulty_div['class'] if ('meal__indicator--' in class_name)][0]
        self.difficulty = difficulty
    def _extract_ingredients(self):
        def clean_ingredient_string(s):
            s = s.replace('Info', '').strip().replace(f'\n', ' ').replace('  ', ' ')
            s = re.sub(r'(&frac)(\d)(\d)', r'\2/\3', s)
            s = s.replace('Home Chef', '')
            if s == '0 Dill Sprigs':
                s = '1 Dill Sprig'
            if s == '0 Chives':
                s = '6 Chive Sprigs'
            return s
        ingredients = self.soup.find_all(itemprop='recipeIngredient')
        recipe_ingredients = [clean_ingredient_string(ingredient.get_text()) for ingredient in ingredients]
        self.ingredients = recipe_ingredients
    def _extract_spice(self):
        spice_div = self.soup.find(class_='meal__overview').find_all('div')[3].find(class_='meal__indicator')
        spice = [class_name.replace('meal__indicator--', '') for class_name in spice_div['class'] if ('meal__indicator--' in class_name)][0]
        self.spice = spice
    def _extract_steps(self):
        steps = self.soup.find(class_='meal__steps').find_all('li')
        recipe_steps = [step.find_all('span')[1].get_text() for step in steps]
        self.steps = recipe_steps
    def _extract_title(self):
        title = self.soup.find('main').find('header')
        self.title = title.get_text().strip()
    def _extract_total_time(self):
        total_time = self.soup.find(itemprop='totalTime').get('content').strip().replace('PT', '').replace('M', '')
        self.total_time = total_time
    def _extract_image_url(self):
        self.image_url = self.soup.find(class_='meal__imageCarousel').find('img')['data-srcset'].split(', ')[-1].split(' ')[0]
    def _commit_recipe(self):
        file_name = persist_image('static/images', myParser.image_url)
        new_recipe = Recipe(title=self.title, prep_time=self.total_time, difficulty=self.difficulty, spice_level=self.spice, category=self.category, image=file_name)                          
        db.session.add(new_recipe)
        db.session.commit()
        self.new_recipe_id = new_recipe.id 
    def _commit_steps(self):
        for i in range(len(self.steps)): 
            db.session.add(Step(recipe_id=self.new_recipe_id, step_number=i, description=myParser.steps[i]))
        db.session.commit()
    def _commit_categories(self):
        categories = set([(ingr['food_category']['id'], ingr['food_category']['description']) for ingr in self.ingredients_parsed])   
        for cat_id, cat_label in categories:
            existing_category = Category.query.get(cat_id)
            if not existing_category:
                new_category = Category(id=cat_id, category_label=cat_label) 
                db.session.add(new_category) 
        db.session.commit()
    def _commit_ingredients(self):
        for ingr in self.ingredients_parsed:
            ingredient = Ingredient.query.filter(Ingredient.food_name == ingr['food_name'], Ingredient.unit == ingr['unit']).first()
            if not ingredient:
                ingredient = Ingredient(food_name=ingr['food_name'], unit=ingr['unit'], category_id=ingr['food_category']['id']) 
                db.session.add(ingredient) 
                db.session.commit()
            recipe_ingredient = RecipeIngredient.query.filter(RecipeIngredient.recipe_id == self.new_recipe_id, RecipeIngredient.ingredient_id == ingredient.id).first()
            if recipe_ingredient:
                current_quantity = recipe_ingredient.quantity
                recipe_ingredient.quanitity = current_quantity + Decimal(ingr['quantity'])
            else: 
                recipe_ingredient = RecipeIngredient(recipe_id=self.new_recipe_id, ingredient_id=ingredient.id, quantity=ingr['quantity']) 
            db.session.add(recipe_ingredient) 
            db.session.commit()  

    @staticmethod
    def parse_ingredient_edamam(ingredient):
        edamam_params = {'app_id':EDEMAM_APP_ID, 'app_key':EDEMAM_APP_KEY, 'ingr':ingredient}
        res = requests.get('https://api.edamam.com/api/food-database/parser', params=edamam_params) 
        if not res.json()['parsed']:
            raise LookupError
        res_data = res.json()['parsed'][0]
        food_name = res_data['food']['label']
        quantity = res_data['quantity']
        unit = res_data['measure']['label']
        return food_name, quantity, unit

    @staticmethod
    def fetch_food_category(food_name):
        usda_general_params = {'api_key': USDA_API_KEY, 'generalSearchInput': food_name, 'includeDataTypeList': 'SR Legacy'}
        res = requests.get('https://api.nal.usda.gov/fdc/v1/search', params=usda_general_params)
        fdcId = res.json()['foods'][0]['fdcId']
        usda_single_params = {'api_key': USDA_API_KEY}
        res = requests.get(f'https://api.nal.usda.gov/fdc/v1/{fdcId}', params=usda_single_params)
        food_category = res.json()['foodCategory']
        return food_category
    
    def parse_ingredients(self):
        self.ingredients_parsed = []
        for ingredient in self.ingredients:
            food_name, quantity, unit = self.parse_ingredient_edamam(ingredient)
            food_category = self.fetch_food_category(food_name)
            self.ingredients_parsed.append({'food_name': food_name, 'quantity':quantity, 'unit': unit, 'food_category':food_category})
            time.sleep(8)



def collect_meal_urls(base_url, category, max_pages, url_list=[]):
    base_category_url = f'{base_url}/recipes/{category}'
    for i in range(1,max_pages+1):
        res = requests.get(base_category_url, params={'page':i})
        soup = BeautifulSoup(res.text, features='html.parser')
        for link in soup.find_all('a'): 
            if '/meals' in link.get('href'): 
                url_list.append((base_url + link.get('href'), category))
def save_all_meal_urls():
    url_list = []
    base_url = 'https://www.homechef.com'
    categories = [('poultry',8), ('seafood', 5), ('pork', 4), ('beef', 3), ('vegetarian', 11)]
    for category, max_pages in categories:
        collect_meal_urls(base_url=base_url, category=category, max_pages=max_pages, url_list=url_list)
    url_list = sorted(url_list, key=lambda tup: tup[0])
    with open('urls.txt', 'w') as f:
        json.dump(url_list, f, indent=4)



# save_all_meal_urls()
with open('urls.txt', 'r') as f:
    url_list = json.loads(f.read())
with open('visited_urls.txt', 'r') as f:
    visited_urls = json.loads(f.read())
with open('unparseable_urls.txt', 'r') as f:
    unparseable_urls = json.loads(f.read())

myParser = RecipeParser()
# for target_url, category in url_list:
#     print(target_url)
#     print('unvisited?')
#     print((target_url not in visited_urls) and (target_url not in unparseable_urls))
#     if (target_url not in visited_urls) and (target_url not in unparseable_urls):
#         try:
#             myParser.set_url(target_url)
#             myParser.parseRecipe()
#             myParser.parse_ingredients()
#             print('finished parsing')
#             myParser.commit_parsed_data()
#             print('finished committing')
#             visited_urls.append((target_url, category))
#             with open('visited_urls.txt', 'w') as f:
#                 json.dump(visited_urls, f, indent=4)
#         except LookupError as e:
#             print('ABORTING PARSE')
#             unparseable_urls.append((target_url, category))
#             with open('unparseable_urls.txt', 'w') as f:
#                 json.dump(unparseable_urls, f, indent=4)
#             time.sleep(8)
#             continue




# for target_url, category in visited_urls:
#     print(target_url)
#      if (target_url not in visited_urls) and (target_url not in unparseable_urls):
#         try:
#             myParser.set_url(target_url)
#             myParser._extract_image_url()
#             myParser._extract_title()
#             target_recipe = Recipe.query.filter_by(title=myParser.title).first()
#             file_name = persist_image('static/images', myParser.image_url)
#             target_recipe.image = file_name
#             db.session.add(target_recipe)
#             db.session.commit()
#         except LookupError as e:
#             print('ABORTING PARSE')

#             continue