from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()


def create_app(test_config=None):
    app = Flask(__name__)

    # A secret for signing session cookies
    app.config["SECRET_KEY"] = "93220d9b340cf9a6c39bac99cce7daf220167498f91fa"

    # Register blueprints
    # (we import main from here to avoid circular imports in the next lab)
    from . import main
    from . import auth

    #THIS DATABASE MUST BE CHANGED TO UC3M DATABASE FOR SUBMISSION
    #MUST INCLUDE FILLER RECIPES IN THIS DATABASE (25+ recipes!!!)
    app.config[ "SQLALCHEMY_DATABASE_URI" ] = "mysql+mysqldb://24_webapp_004:EzvZpvA2@mysql.lab.it.uc3m.es/24_webapp_062a"
    #app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///microblog.db"
    
    db.init_app(app)

    # uploading log in stuff  
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    from . import model

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(model.User, int(user_id))
    

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    return app