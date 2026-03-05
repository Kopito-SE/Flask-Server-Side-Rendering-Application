from flask import Blueprint, session, redirect, url_for, flash
from ..models import User

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return "Home Page"

@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first!")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    return f"Welcome {user.username} 🚀"