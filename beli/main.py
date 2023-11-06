import datetime
import dateutil.tz

from flask import Blueprint, render_template


from . import model

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user = model.User(1, "mary@example.com", "mary")
    posts = [
        model.Recipe(
            1, "Cheese", "its just cheese", user, 4, 15
        ),
        model.Recipe(
            2, "Jamon", "Jamon Iberico", user, 1, 10
        ),
    ]
    return render_template("main/index.html", recipes=posts)