import datetime
import dateutil.tz

from flask import Blueprint, render_template


from . import model

bp = Blueprint("main", __name__)


@bp.route("/")
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
