from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

mail = Mail()

db = SQLAlchemy()


def _ensure_column_exists(table, column, column_sql):
    inspector = inspect(db.engine)
    if table not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns(table)}
    if column in column_names:
        return

    with db.engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
     raise ValueError("SECRET_KEY is not set!")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
     raise ValueError("SQLALCHEMY_DATABASE_URI is not set!")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

   

# Email configuration
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
    #display_name = os.environ.get("MAIL_DEFAULT_SENDER_NAME")
    #username = app.config["MAIL_USERNAME"]

    #if display_name and username:
    #  app.config["MAIL_DEFAULT_SENDER"] = (display_name, username)
    #elif username:
    #  app.config["MAIL_DEFAULT_SENDER"] = username

  
    mail.init_app(app)

    # Ensure model metadata is loaded before create_all()
    from . import models  # noqa: F401

    with app.app_context():
        db.create_all()
        try:
            _ensure_column_exists("product", "image", "image VARCHAR(200)")
            _ensure_column_exists("product", "category_id", "category_id INTEGER")
        except Exception as e:
            print(f"Schema sync warning: {e}")
        print("Database table created")

    # Register Blueprints
    from .auth.routes import auth
    from .main.routes import main

    register_filters(app)
    app.register_blueprint(auth)
    app.register_blueprint(main)



    @app.context_processor
    def inject_user():
        from .models import User
        from flask import session

        user = None

        if "user_id" in session:
            user = User.query.get(session["user_id"])
        return dict(current_user=user)

    return app


def format_price(value):
    try:
        return f"{value:,.2f}"
    except (TypeError, ValueError):
        return value


def register_filters(app):
    app.add_template_filter(format_price, "format_price")