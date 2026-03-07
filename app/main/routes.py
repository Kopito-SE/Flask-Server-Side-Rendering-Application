from flask import Blueprint, session, redirect, url_for, flash, render_template, request

from app import auth
from ..models import CartItem, CustomerOrder, OrderItem, User, Product
from .. import db

main = Blueprint("main", __name__)


@main.route("/")
def home():
    products = Product.query.all()
    return render_template("home.html", products=products)
@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    products = Product.query.all()
    
    return render_template("dashboard.html", user=user, products=products)
@main.route("/add-product", methods=["GET","POST"])
def add_product():
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])

    if user.role != "admin":
        flash("Access Denied: Admins Only")
        return redirect(url_for("main.home"))
    
    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")

        if not name or not price:
            flash("Name and Price are required!")
            return redirect(url_for("main.add_product"))

        new_product = Product(
            name=name,
            price=float(price), 
            description=description
        )   
        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully!")
        return redirect(url_for("main.home"))

    return render_template("add_product.html")
@main.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    item = CartItem.query.filter_by(
            user_id=user_id, 
            product_id=product_id
    ).first()

    if item:
        item.quantity += 1
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity= 1
        )
        db.session.add(item)
    db.session.commit()
    flash("Product added to cart!")
    return redirect(url_for("main.home"))
@main.route("/cart")
def view_cart():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    return render_template("cart.html", cart_items=cart_items)
@main.route("/checkout")
def checkout():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        flash("Your cart is empty!")
        return redirect(url_for("main.home"))
    
    new_order = CustomerOrder(user_id=user_id)

    db.session.add(new_order)
    db.session.commit()

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.session.add(order_item)
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    flash("Order placed successfully!")
    return redirect(url_for("main.home"))
@main.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    orders = CustomerOrder.query.filter_by(user_id=user_id).all()
    return render_template("orders.html",orders=orders)