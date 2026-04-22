from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from ..models import User
from .. import db
import random
from flask_mail import Message
from .. import mail


auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        
        # Validate inputs
        if not all([username, password, email]):
            flash('All fields are required!')
            return redirect(url_for('auth.register'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('auth.register'))
        
        if User.query.filter(func.lower(User.email) == email).first():
            flash('Email already registered!')
            return redirect(url_for('auth.register'))
        
        # Generate and store verification code
        code = random.randint(100000, 999999)
        session['verify_email'] = email
        session["verify_username"] = username
        session["verify_password"] = generate_password_hash(password)
        session["verification_code"] = str(code)
        
        
        # Send email
        msg = Message(
            'Kopito Web Verification code', 
            recipients=[email]
        )

        msg.body = f'Your verification code is: {code}'
        mail.send(msg)
        
        flash('Verification code sent to your email!')
        return redirect(url_for('auth.verify_email'))
    
    return render_template('register.html')

@auth.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    #Check if all data exists
    if not all(k in session for k in ["verify_email", "verify_username", "verify_password", "verification_code"]):
        flash("No registration in progress,Register first")
        return redirect("auth.register")
    
    
    if request.method == 'POST':
        user_code = request.form.get('code')
        
        if user_code == session.get("verification_code"):

            new_user = User(
                email=session["verify_email"],
                username=session["verify_username"],
                password=session["verify_password"]
            )

        
            db.session.add(new_user)
            db.session.commit()
            
            # Clear session
            session.pop("verify_email", None)
            session.pop("verify_username", None)
            session.pop("verify_password", None)
            session.pop("verification_code", None)
            
            flash('Email verified! You can now login.')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid verification code!')
            return redirect(url_for('auth.verify_email'))
    
    return render_template('verify_email.html')



@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email and password are required!")
            return redirect(url_for("auth.login"))

        user = User.query.filter(func.lower(User.email) == email.lower()).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!")
            return redirect(url_for("main.dashboard"))

        flash("Invalid credentials!")
        return redirect(url_for("auth.login"))

    return render_template("login.html")




@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!")
    return redirect(url_for("auth.login"))
