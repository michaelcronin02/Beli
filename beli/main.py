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
    #.join(model.User)
    #.join(followers, model.User.followers)
    #.where(followers.id == flask_login.current_user.id)
    .limit(10))
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
                        )

    db.session.add(recipe)
    db.session.commit()
    return redirect(url_for("main.recipe", recipe_id=recipe.id))

@bp.route("/recipe/<int:recipe_id>")
@flask_login.login_required
def recipe(recipe_id):
    recipe = db.session.get(model.Recipe, recipe_id)
    if not recipe:
        abort(404, "Recipe id {} doesn't exist.".format(recipe_id))
    return render_template("main/recipe.html", recipe=recipe)

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
