import datetime
import dateutil.tz

import flask_login
from flask_login import current_user

from flask import Blueprint, abort, render_template, request, redirect, url_for, flash
from . import db, bcrypt
from . import model

bp = Blueprint("main", __name__)


@bp.route("/")
@flask_login.login_required
def index():
    user = model.User(email="mary@example.com", name="mary", )
    posts = [
        model.Recipe(
            user=user,
            title="Beans",
            description="many beans",
            user_id=user,
            servings = 4,
            cook_time = 15,
        ),
        model.Recipe(
            user=user,
            title="Eggs",
            description="many eggs",
            user_id=user,
            servings = 1,
            cook_time = 30,
        ),
    ]
    return render_template("main/index.html", posts=posts)
