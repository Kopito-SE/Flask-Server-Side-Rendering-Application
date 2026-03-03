from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "supersecretkey"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:osama4545@localhost/flask_auth"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    #import models
    from .models import users

    #Register blueprints
    from .auth.routes import auth
    from .main.routes import main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app