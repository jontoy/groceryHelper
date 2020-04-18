# GroceryHelper  
 A grocery list planning site [currently deployed on heroku](https://whispering-basin-65178.herokuapp.com/).

## The Idea  
 As an avid home cook, I have always found grocery shopping to be the largest pain point in the entire home cooking process. You end up looping back and forth across the store looking for items, and it's easy to overlook items in the unsorted lists that generally accompany recipes on recipe sites. You're exhausted before you even start on the "cooking" portion of the home cooking process.

 Enter GroceryHelper. With this site you can browse through delicious recipes, pick out your favorites, and - with a push of a button - generate a sorted grocery list of aggregated ingredient quantities broken down by the food isle they are most likely to be found in. This allows you to enter the grocery store with a plan, minimize the need to wander throughout the store, and generally make the process as painless as possible.
## The Data  
 Recipe information is initially scraped from the [Home Chef](https://www.homechef.com/recipes) website. 
 The ingredient list is then passed through the natural language analysis engine of the [Edemam Food Database API](https://developer.edamam.com/food-database-api) to extract food names, quantities and units, which are then passed through the [FoodData Central API](https://fdc.nal.usda.gov/api-guide.html) to classify each ingredient under a USDA category.

 As web scraping generally results in messy data, manual cleaning was performed to catch misclassification of foods and categories, often through cross-referencing to their original sources. Measurement unit conversions are manually compiled on a per-ingredient basis.

## Features
 - Search through recipes in database using various data filters
 - Ability to favorite recipes for later retrieval
 - Visual indicator of recipes currently in the user's cart
 - Create and name multiple grocery carts and fill them independently.
 - Edit existing cart names and associated recipe quantities
 - View a grocery list associated with each cart that aggregates ingredients and organizes information by food category
 - View historical carts and their associated grocery lists
 - Copy contents of a historical cart to create a new one

## General User Flow
 1. Make an account (email addresses are not used in any way, so feel free to enter anything that conforms to an email format).  
 2. Go to Recipes to view existing recipes in the database. You can filter results by primary protein, difficulty, spiciness, etc.  
 3. If you want to view more information on a particular recipe, click "View Recipe" to see details such as the ingredient lists and directions.  
 4. If you like a particular recipe, press the "Add to Cart" button to add it to your current grocery cart. Pressing the button multiple times will increase the quantity appropriately.  
 5. Head to Carts to view the status of your current cart as well as historical carts. From there you can edit things like your cart's name and the quantities of items in your current cart.  
 6. When your cart's recipes are to your liking press the "Generate Grocery List!" button to view a summary of all the ingredients needed to cook your chosen recipe, broken down by grocery category. The grocery list supports a condensed, printer-friendly format.

## Tech Stack
 - Flask backend
 - PostgreSQL database
 - Amazon S3 Image Hosting
 - Gunicorn server
 - Heroku deployment platform
 - Bootstrap for styling

## Web Scraping  
 The scripts for generating the raw recipe data are found within the `scrape.py` file. The file url.txt contains all possible target recipe urls and is generated using the `save_all_meal_urls()` method.  
 In order to utilize the `scrape.py` script, one must apply for an EDEMAM Food Database API key and store the EDEMAM_APP_ID and EDEMAM_APP_KEY in a file called `secrets.py`.  
 You must also apply for a [FoodData Central API KEY](https://fdc.nal.usda.gov/api-key-signup.html) and store it as USDA_API_KEY in `secrets.py`.
