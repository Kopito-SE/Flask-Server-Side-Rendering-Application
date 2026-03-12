from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

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

    app.config["SECRET_KEY"] = "supersecretkey"
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:osama4545@localhost/flask_authentication"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

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

    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app
