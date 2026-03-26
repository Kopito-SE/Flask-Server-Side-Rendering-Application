import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for, jsonify
from werkzeug.utils import secure_filename

from .. import db
from ..models import CartItem, Category, CustomerOrder, OrderItem, Product, User
from flask_login import login_required, current_user
main = Blueprint("main", __name__)


@main.route("/")
def home():
    products = Product.query.all()
    categories = Category.query.all()
    return render_template("home.html", products=products, categories=categories)


@main.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    products = Product.query.all()

    return render_template("dashboard.html", user=user, products=products)


@main.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])

    if user.role != "admin":
        flash("Admin access required")
        return redirect(url_for("main.home"))

    categories = Category.query.all()

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        file = request.files.get("image")
        category_id = request.form.get("category_id")

        if not name or not price:
            flash("Name and Price are required!")
            return redirect(url_for("main.add_product"))

        if not category_id:
            flash("Please select a category!")
            return redirect(url_for("main.add_product"))

        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            if not filename:
                flash("Invalid image filename!")
                return redirect(url_for("main.add_product"))

            upload_folder = os.path.join(current_app.static_folder, "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)

            try:
                file.save(filepath)
            except Exception as e:
                flash(f"Error saving file: {str(e)}")
                return redirect(url_for("main.add_product"))

        try:
            price_float = float(price)
        except ValueError:
            flash("Price must be a valid number!")
            return redirect(url_for("main.add_product"))

        new_product = Product(
            name=name,
            price=price_float,
            description=description,
            image=filename,
            category_id=int(category_id),
        )

        try:
            db.session.add(new_product)
            db.session.commit()
            flash("Product added successfully!")
            return redirect(url_for("main.home"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving to database: {str(e)}")
            return redirect(url_for("main.add_product"))

    return render_template("add_product.html", categories=categories)


@main.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
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
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template("cart.html", cart_items=cart_items,total=total)

@main.route("/update-cart", methods=["POST"])
@login_required
def update_cart():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        action = data.get('action')
        
        cart_item = CartItem.query.get_or_404(item_id)
        
        if cart_item.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                db.session.delete(cart_item)
                db.session.commit()
                return jsonify({'success': True, 'removed': True})
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

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
            quantity=item.quantity,
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
    return render_template("orders.html", orders=orders)


@main.route("/category/<int:category_id>")
def category_view(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category.id).all()
    return render_template("category.html", category=category, products=products)


@main.route("/admin/categories")
def admin_categories():
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))
    categories = Category.query.all()
    return render_template("admin_categories.html", categories=categories)
@main.route("/admin/add-category", methods=["GET", "POST"])
def add_category():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Category Name is Required!")
            return redirect(url_for("main.add_category"))
        new_category = Category(name=name)
        try:
            db.session.add(new_category)
            db.session.commit()
            flash("Category added successfully!")
            return redirect(url_for("main.admin_categories"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving to database: {str(e)}")
            return redirect(url_for("main.add_category"))
    return render_template("add_category.html")
@main.route("/admin/edit-category/<int:category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))
    category = Category.query.get_or_404(category_id)
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Category name is required!")
            return redirect(url_for("main.edit_category", category_id=category_id))
        
        category.name = name
        try:
            db.session.commit()
            flash("Category updated successfully!")
            return redirect(url_for("main.admin_categories"))
        except Exception as e:
            db.session.rollback()
            flash(f"An Error has occured updating Category Database")
            return redirect(url_for("main.admin_categories"))
    return render_template("edit_category.html",category=category)
@main.route("/admin/delete-category/<int:category_id>")
def delete_category(category_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for(main.home))
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted!")
    return redirect(url_for("main.admin_categories"))

@main.route("/admin/orders")
def admin_orders():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    
   
    if user.role != "admin":
        flash("Admin privileges required")
        return redirect(url_for("main.home"))
    
    orders = CustomerOrder.query.all()
    return render_template("admin_orders.html", orders=orders)

@main.route("/admin/update-order/<int:order_id>",methods=["POST", "GET"])
def update_order_status(order_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))
    order = CustomerOrder.query.get_or_404(order_id)
    if request.method == "POST":
        status = request.form.get("status")
        order.order_status = status

        db.session.commit()
        flash("Order Status Updated!")
        return redirect(url_for("main.admin_orders"))
    return render_template("update_order.html",order=order)

        
@main.route("/admin/products")
def admin_products():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin access required!")
        return redirect(url_for("main.home"))

    products = Product.query.all()
    return render_template("admin_products.html", products=products)


@main.route("/admin/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))

    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name = request.form.get("name")
        product.price = float(request.form.get("price"))
        product.description = request.form.get("description")
        product.category_id = int(request.form.get("category_id"))

        image_file = request.files.get("image")
        if image_file:
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(current_app.static_folder, "uploads", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image_file.save(file_path)
            product.image = filename
        db.session.commit()
        flash("Product updated successfully!")
        return redirect(url_for("main.admin_products"))
    return render_template("edit_product.html", product=product, categories=categories)

@main.route("/admin/delete-product/<int:product_id>", methods=["GET", "POST"])
def delete_product(product_id):
    if "user_id" not in session:
        flash("Please Login First")
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin Privillages Required")
        return redirect(url_for("main.home"))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!")
    return redirect(url_for("main.admin_products"))

@main.route("/admin/dashboard")
def admin_dashboard():
    
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        return redirect(url_for("main.home"))
    total_users = User.query.count()
    total_products = Product.query.count()
    total_categories = Category.query.count()
    total_orders = CustomerOrder.query.count()
     
     #Calculate Revenue
    order_items = OrderItem.query.all()

    revenue = 0
    for item in order_items:
        revenue += item.product.price * item.quantity

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_products=total_products,
        total_categories=total_categories,
        total_orders=total_orders,
        revenue=revenue
    )


@main.route("/admin/users")
def admin_users():
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    
    user = User.query.get(session["user_id"])
    if user.role != "admin":
        flash("Admin privileges required")
        return redirect(url_for("main.home"))
    
    # Get all users except the current admin (to prevent self-deletion)
    users = User.query.filter(User.id != user.id).all()
    return render_template("admin_users.html", users=users)

@main.route("/admin/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user_id" not in session:
        flash("Please login first")
        return redirect(url_for("auth.login"))
    
    admin_user = User.query.get(session["user_id"])
    if admin_user.role != "admin":
        flash("Admin privileges required")
        return redirect(url_for("main.home"))
    
    user_to_delete = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user_to_delete.id == admin_user.id:
        flash("You cannot delete your own account!")
        return redirect(url_for("main.admin_users"))
    
    try:
        # Delete user's cart items first (due to foreign key constraints)
        CartItem.query.filter_by(user_id=user_to_delete.id).delete()
        
        # Delete user's order items and orders
        orders = CustomerOrder.query.filter_by(user_id=user_to_delete.id).all()
        for order in orders:
            OrderItem.query.filter_by(order_id=order.id).delete()
            db.session.delete(order)
        
        # Finally delete the user
        db.session.delete(user_to_delete)
        db.session.commit()
        
        flash(f"User {user_to_delete.username} has been deleted successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}")
    
    return redirect(url_for("main.admin_users"))  
