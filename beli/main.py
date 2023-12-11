import datetime
import dateutil.tz

import flask_login
from flask_login import current_user

from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, current_app
from . import db, bcrypt
from . import model
import pathlib

bp = Blueprint("main", __name__)


@bp.route("/")
@flask_login.login_required
def index():
    followers = db.aliased(model.User)
    query = (
    db.select(model.Recipe)
    .order_by(model.Recipe.id.desc())
    .limit(4))
    recipes = db.session.execute(query).scalars().all()
    return render_template("main/index.html", recipes=recipes)


@bp.route("/user/<int:user_id>")
@flask_login.login_required
def userProfile(user_id):
    user = db.session.get(model.User, user_id)
    if not user:
        abort(404, "User id {} doesn't exist.".format(user_id))
    query = db.select(model.Recipe).where((model.Recipe.user_id == user_id))
    recipes = db.session.execute(query).scalars().all()

    if user == current_user:
        follow_button = None
    if flask_login.current_user not in user.followers:
        follow_button = "follow"
    if flask_login.current_user in user.followers:
        follow_button = "unfollow"

    return render_template("main/profile.html", recipes=recipes, user=user, follow_button=follow_button)


@bp.route("/new_recipe", methods=['POST'])
@flask_login.login_required
def new_recipe():
    recipe_title = request.form.get("title")
    recipe_description = request.form.get("description")
    recipe_servings = request.form.get("servings")
    recipe_cook_time = request.form.get("cook_time")
    recipe = model.Recipe(user=flask_login.current_user,
                         title = recipe_title,
                         description = recipe_description,
                         servings = recipe_servings,
                         cook_time = recipe_cook_time,
                         complete = False,
                        )

    db.session.add(recipe)
    db.session.commit()
    return redirect(url_for("main.recipe_creation", recipe_id=recipe.id))

@bp.route("/recipe_creation/<int:recipe_id>", methods=['GET'])
@flask_login.login_required
def recipe_creation(recipe_id):
    recipe = db.get_or_404(model.Recipe, recipe_id)

    query = db.select(model.Ingredient)
    ingredients = db.session.execute(query).scalars().all()

    query2 = db.select(model.Step).where((model.Step.recipe_id == recipe_id)).order_by(model.Step.order)
    steps = db.session.execute(query2).scalars().all()

    return render_template("main/recipe_creation.html", recipe = recipe, ingredients = ingredients, steps = steps)

@bp.route("/new_ingredient/<int:recipe_id>", methods=['POST'])
@flask_login.login_required
def new_ingredient(recipe_id):
    new_recipe_ingredient = request.form.get("ingredient")
    new_recipe_amount = request.form.get("amount")
    new_recipe_quantity = request.form.get("quantity")

    recipe = db.get_or_404(model.Recipe, recipe_id)

    ## take the name of the ingredient and look for it in the data base
    query = db.select(model.Ingredient).where((model.Ingredient.name == new_recipe_ingredient))
    ingredient = db.session.execute(query).scalars().one_or_none()

    ## if it doesn't exist you create a new ingredient object
    if ingredient is None:
        ingredient = model.Ingredient(
            name = new_recipe_ingredient
        )
        db.session.add(ingredient)

    quantified_ingredients = model.QuantifiedIngredient(
                amount = new_recipe_amount,
                unit = new_recipe_quantity,
                ingredient = ingredient,
                recipe = recipe,
                )

    db.session.add(quantified_ingredients)
    db.session.commit()

    return redirect(url_for("main.recipe_creation", recipe_id = recipe_id))

## updating database with new step
@bp.route("/new_step/<int:recipe_id>", methods=['POST'])
@flask_login.login_required
def new_step(recipe_id):
    new_recipe_step = request.form.get("step")

    recipe = db.get_or_404(model.Recipe, recipe_id)

    ## order of steps is the length of list + 1
    steps = model.Step(
        order = len(recipe.steps) + 1,
        description = new_recipe_step,
        recipe = recipe
    )

    db.session.add(steps)
    db.session.commit()
    
    return redirect(url_for("main.recipe_creation", recipe_id = recipe_id))

@bp.route("/complete_recipe/<int:recipe_id>", methods=['POST'])
@flask_login.login_required
def complete_recipe(recipe_id):
    recipe = db.get_or_404(model.Recipe, recipe_id)
    recipe.complete = True
    db.session.commit()

    return redirect(url_for("main.recipe", recipe_id = recipe.id))

@bp.route("/recipe/<int:recipe_id>")
@flask_login.login_required
def recipe(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    user = flask_login.current_user
    query = db.select(model.Rating).where((model.Rating.user_id == user.id) & (model.Rating.recipe_id == recipe_id))
    rating = db.session.execute(query).scalars().one_or_none()
    query_likes = db.select(model.Rating).where((model.Rating.recipe_id==recipe.id) & (model.Rating.value==1))
    num_likes1 = db.session.execute(query_likes).scalars().all()
    query_dislikes = db.select(model.Rating).where((model.Rating.recipe_id==recipe.id) & (model.Rating.value==0))
    num_dislikes1 = db.session.execute(query_dislikes).scalars().all()
    num_likes = len(num_likes1) if isinstance(num_likes1, list) else 0
    num_dislikes = len(num_dislikes1) if isinstance(num_dislikes1, list) else 0
    if not rating:
        return render_template("main/recipe.html", recipe=recipe, num_likes=num_likes, num_dislikes=num_dislikes)
    else:
        return render_template("main/recipe.html", recipe=recipe, rating=rating, num_likes=num_likes, num_dislikes=num_dislikes)

@bp.route("/follow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def follow(user_id):
    user = db.session.get(model.User, user_id)
    query = db.select(model.Recipe).where((model.Recipe.user_id == user_id))
    recipes = db.session.execute(query).scalars().all()
    if not user:
        abort(404, "User id {} doesn't exist.".format(user_id))
    if user == current_user:
        abort(403, "User id {} is your user.".format(user_id))
    if flask_login.current_user in user.followers:
        abort(403, "User id {} is already followed.".format(user_id))
    user.followers.append(flask_login.current_user)
    db.session.commit()
    return redirect(url_for("main.userProfile", user_id=user_id))

@bp.route("/unfollow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def unfollow(user_id):
    user = db.session.get(model.User, user_id)
    query = db.select(model.Recipe).where((model.Recipe.user_id == user_id))
    recipes = db.session.execute(query).scalars().all()
    if not user:
        abort(404, "User id {} doesn't exist.".format(user_id))
    if user == current_user:
        abort(403, "User id {} is your user.".format(user_id))
    if flask_login.current_user not in user.followers:
        abort(403, "User id {} is not already followed.".format(user_id))
    user.followers.remove(flask_login.current_user)
    db.session.commit()
    return redirect(url_for("main.userProfile", user_id=user_id))
# return render_template("main/profile.html", user=user, posts=posts, follow_button=follow_button)

@bp.route("/upload_photo", methods = ['POST'])
@flask_login.login_required
def upload_photo():
    uploaded_file = request.files['photo']
    if uploaded_file.filename == '':
        abort(400, f"No file uplaoded")
    content_type = uploaded_file.content_type
    if content_type == "image/png":
        file_extension = "png"
    elif content_type == "image/jpeg":
        file_extension = "jpg"
    else:
        abort(400, f"Unsupported file type {content_type}")
    recipe_id = request.form.get("recipe_id")
    recipe = db.session.get(model.Recipe, recipe_id)
    photo = model.Photo(
        user=flask_login.current_user,
        recipe=recipe,
        file_extension=file_extension
    )
    db.session.add(photo)
    db.session.commit()
    path = (
        pathlib.Path(current_app.root_path)
        / "static"
        / "photos"
        / f"photo-{photo.id}.{file_extension}"
    )
    uploaded_file.save(path)
    #redirect user to recipe view again so that they can see the photo
    return redirect(url_for("main.recipe", recipe_id = recipe_id))

@bp.route("/like_post/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def like(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    user = flask_login.current_user
    if not user:
        abort(404, "You are not an authorized user. Make an account to give a rating.")
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    query = db.select(model.Rating).where((model.Rating.user_id == user.id) & (model.Rating.recipe_id == recipe_id))
    rating = db.session.execute(query).scalars().one_or_none()
    if rating == 1:
        abort(404, "Recipe id {} is already liked.".format(recipe_id))
    if rating == 0:
        rating.value = 1
    if not rating:
        rating = model.Rating(user=user, value=1, recipe=recipe)
    db.session.add(rating)
    db.session.commit()
    return redirect(url_for("main.recipe", recipe_id=recipe_id))

@bp.route("/dislike_post/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def dislike(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    user = flask_login.current_user
    if not user:
        abort(404, "You are not an authorized user. Make an account to give a rating.")
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    query = db.select(model.Rating).where((model.Rating.user_id == user.id) & (model.Rating.recipe_id == recipe_id))
    rating = db.session.execute(query).scalars().one_or_none()
    if rating == 0:
        abort(404, "Recipe id {} is already disliked.".format(recipe_id))
    if rating == 1:
        rating.value = 0
    if not rating:
        rating = model.Rating(user=user, value=0, recipe=recipe)
    db.session.add(rating)
    db.session.commit()
    return redirect(url_for("main.recipe", recipe_id=recipe_id))

@bp.route("/remove_rating/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def removeRating(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    user = flask_login.current_user
    if not user:
        abort(404, "You are not an authorized user. Make an account to give a rating.")
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    query = db.select(model.Rating).where((model.Rating.user_id == user.id) & (model.Rating.recipe_id == recipe_id))
    rating = db.session.execute(query).scalars().one_or_none()
    if not rating:
        abort(404, "Rating doesn't exist.")
    db.session.delete(rating)
    db.session.commit()
    return redirect(url_for("main.recipe", recipe_id=recipe_id))

@bp.route("/bookmark_recipe/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def bookmarkRecipe(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    user = flask_login.current_user
    if not user:
        abort(404, "You are not an authorized user. Make an account to give a rating.")
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    query = db.select(model.Bookmark).where((model.Bookmark.user_id == user.id) & (model.Bookmark.recipe_id == recipe_id))
    bookmark = db.session.execute(query).scalars().one_or_none()
    if bookmark in user.bookmarks:
        abort(403, "Recipe id {} is already bookmarked.".format(recipe_id))
    bookmark = model.Bookmark(user=user, recipe=recipe)
    db.session.add(bookmark)
    db.session.commit()
    return render_template("main/recipe.html", user=user, recipe=recipe, bookmark_button="Unbookmark")

@bp.route("/unbookmark_recipe/<int:recipe_id>", methods=["POST"])
@flask_login.login_required
def unbookmarkRecipe(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    user = flask_login.current_user
    if not user:
        abort(404, "You are not an authorized user. Make an account to give a rating.")
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    query = db.select(model.Bookmark).where((model.Bookmark.user_id == user.id) & (model.Bookmark.recipe_id == recipe_id))
    bookmark = db.session.execute(query).scalars().one_or_none()
    if bookmark not in user.bookmarks:
        abort(403, "Recipe id {} is already not bookmarked.".format(recipe_id))
    db.session.delete(bookmark)
    db.session.commit()
    return render_template("main/recipe.html", user=user, recipe=recipe, bookmark_button="Bookmark")