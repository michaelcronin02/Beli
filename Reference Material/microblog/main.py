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
    followers = db.aliased(model.User)
    query = (
    db.select(model.Message)
    .join(model.User)
    .join(followers, model.User.followers)
    .where(followers.id == flask_login.current_user.id)
    .where(model.Message.response_to == None)
    .order_by(model.Message.timestamp.desc())
    .limit(10))
    posts = db.session.execute(query).scalars().all()
    return render_template("main/index.html", posts=posts)

@bp.route("/user/<int:user_id>")
@flask_login.login_required
def userProfile(user_id):
    user = db.session.get(model.User, user_id)
    if not user:
        abort(404, "User id {} doesn't exist.".format(user_id))
    query = db.select(model.Message).where((model.Message.user_id == user_id) & (model.Message.response_to == None)).order_by(model.Message.timestamp.desc())
    posts = db.session.execute(query).scalars().all()

    if user == current_user:
        follow_button = None
    if flask_login.current_user not in user.followers:
        follow_button = "follow"
    if flask_login.current_user in user.followers:
        follow_button = "unfollow"

    return render_template("main/profile.html", posts=posts, user=user, follow_button=follow_button)


@bp.route("/new_post", methods=['POST'])
@flask_login.login_required
def new_post():
    message_text = request.form.get("text")
    message = model.Message(user=flask_login.current_user,
                         text = message_text,
                         timestamp=datetime.datetime.now(dateutil.tz.tzlocal()))
    if request.form.get("response_to") is None:
        message.response_to=None
    else:
        og_message = db.session.get(model.Message, int(request.form.get("response_to")))
        if not og_message:
            abort(404, "Post id {} doesn't exist.".format(message.id))
        message.response_to = og_message
    db.session.add(message)
    db.session.commit()
    if(message.response_to != None):
        return redirect(url_for("main.post", message_id=og_message.id))
    else:
        return redirect(url_for("main.post", message_id=message.id))

@bp.route("/post/<int:message_id>")
@flask_login.login_required
def post(message_id):
    message = db.session.get(model.Message, message_id)
    if not message:
        abort(404, "Post id {} doesn't exist.".format(message_id))
    if message.response_to != None:
        abort(403, "Post id {} is a message response.".format(message_id))
    return render_template("main/post.html", post=message)

@bp.route("/follow/<int:user_id>", methods=["POST"])
@flask_login.login_required
def follow(user_id):
    user = db.session.get(model.User, user_id)
    query = db.select(model.Message).where((model.Message.user_id == user_id) & (model.Message.response_to == None)).order_by(model.Message.timestamp.desc())
    posts = db.session.execute(query).scalars().all()
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
    query = db.select(model.Message).where((model.Message.user_id == user_id) & (model.Message.response_to == None)).order_by(model.Message.timestamp.desc())
    posts = db.session.execute(query).scalars().all()
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