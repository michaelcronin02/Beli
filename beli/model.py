class Recipe:
    def __init__(self, recipe_id, title, description, user, servings, cooktime):
        self.recipe_id = recipe_id
        self.title = title
        self.description = description
        self.user = user
        self.servings = servings
        self.cooktime = cooktime

class User:
    def __init__(self, user_id, email, name):
        self.user_id = user_id
        self.email = email
        self.name = name
