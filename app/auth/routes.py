from flask import Blueprint, render_templates, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import  User
from ..import db

auth = Blueprint("auth", __name__)
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("All fields are required")
            return redirect(url_for("auth.register"))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("auth.register"))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful!")
        return redirect(url_for("auth.login"))
    return render_templates("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!")
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password")
        return redirect(url_for("auth.login"))
    return render_templates("login.html")
@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.")
    return redirect(url_for("auth.login"))