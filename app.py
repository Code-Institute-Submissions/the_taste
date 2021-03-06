import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    recipes = mongo.db.recipes.find().sort("recipe_name", 1)
    allergens = mongo.db.allergens.find().sort("allergen_name", 1)
    categories = mongo.db.categories.find().sort("category_name", 1)
    ingredients = mongo.db.recipes.find().sort("ingredient_name", 1)
    return render_template("recipes.html",
                           ingredients=ingredients, allergens=allergens,
                           categories=categories, recipes=recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username is in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # makes shure thet hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password
                flash("Incorect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username don't exist
            flash("Incorect Username and/or Password")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # gets user's username from the DB
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "category_name": request.form.get("category_name"),
            "recipe_description": request.form.get("recipe_description"),
            "preparation_time": request.form.get("preparation_time"),
            "cooking_time": request.form.get("cooking_time"),
            "allergens": request.form.getlist("allergen_name"),
            "ingredient_name": request.form.getlist("ingredient_name"),
            "ingredient_uantity": request.form.getlist("ingredient_quantity"),
            "preparation": request.form.get("recipe_preparation"),
            "created_by": session["user"]
        }
        mongo.db.recipes.insert_one(recipe)
        return redirect(url_for("get_recipes"))
    allergens = mongo.db.allergens.find().sort("allergen_name", 1)
    categories = mongo.db.categories.find().sort("category_name", 1)
    ingredients = mongo.db.ingredients.find().sort("ingredient_name", 1)
    return render_template("add_recipe.html",
                           allergens=allergens, categories=categories,
                           ingredients=ingredients)


@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        submit = {
            "recipe_name": request.form.get("recipe_name"),
            "category_name": request.form.get("category_name"),
            "recipe_description": request.form.get("recipe_description"),
            "preparation_time": request.form.get("preparation_time"),
            "cooking_time": request.form.get("cooking_time"),
            "allergens": request.form.getlist("allergen_name"),
            "preparation": request.form.get("recipe_preparation"),
            "created_by": session["user"]
        }
        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, submit)
        flash("Recipe Updated")
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    allergens = mongo.db.allergens.find().sort("allergen_name", 1)
    ingredients = mongo.db.ingredients.find().sort("ingredient_name", 1)
    return render_template("edit_recipe.html",
                           recipe=recipe, categories=categories,
                           allergens=allergens, ingredients=ingredients)


@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("get_recipes"))


@app.route("/delete_ingredient/<ingredient_id>")
def delete_ingredient(ingredient_id):
    mongo.db.ingredients.remove({"_id": ObjectId(ingredient_id)})
    flash("Ingredient Deleted")
    return redirect(url_for("get_ingredients"))


@app.route("/get_ingredients")
def get_ingredients():
    ingredients = mongo.db.ingredients.find().sort("ingredient_name", 1)
    recipe = mongo.db.recipes.find().sort("recipe_name", 1)
    return render_template("ingredients.html", ingredients=ingredients,
                           recipe=recipe)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
