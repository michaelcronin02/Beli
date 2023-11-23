from . import db
import flask_login

class FollowingAssociation(db.Model):
    follower_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )
    followed_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False
    )

class User(flask_login.UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    recipes = db.relationship('Recipe', back_populates='user')
    #ratings = db.relationship('Rating', back_populates='user')
    following = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.follower_id == id,
        secondaryjoin=FollowingAssociation.followed_id == id,
        back_populates="followers",
    )
    followers = db.relationship(
        "User",
        secondary=FollowingAssociation.__table__,
        primaryjoin=FollowingAssociation.followed_id == id,
        secondaryjoin=FollowingAssociation.follower_id == id,
        back_populates="following",
    )

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text(512), nullable=False)
    description = db.Column(db.Text, nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    cook_time = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='recipes')
    #quantified_ingredients = db.relationship('QuantifiedIngredient', back_populates='recipe')
    #ratings = db.relationship('Rating', back_populates='recipe')

#class Ingredient(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String(512), nullable=False)
#    quantified_ingredients = db.relationship('QuantifiedIngredient', back_populates='ingredient')

#class QuantifiedIngredient(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    amount = db.Column(db.Float, nullable=False)
#    unit = db.Column(db.String(64), nullable=False)
#    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
#    ingredient = db.relationship('Ingredient', back_populates='quantified_ingredients')
#    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
#    recipe = db.relationship('Recipe', back_populates='quantified_ingredients')

#class Rating(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    value = db.Column(db.Integer, nullable=False) # 0 is a like, 1 is a dislike
#    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
#    recipe = db.relationship('Recipe', back_populates='ratings')
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#    user = db.relationship('User', back_populates='ratings')