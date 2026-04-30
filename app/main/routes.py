import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from .. import db
from ..models import CartItem, Category, CustomerOrder, OrderItem, Product, User

try:
    import cloudinary
    import cloudinary.uploader
except Exception:
    cloudinary = None

main = Blueprint("main", __name__)


def _configure_cloudinary():
    if cloudinary is None:
        return False

    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
    api_key = os.environ.get("CLOUDINARY_API_KEY")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        return False

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    return True


def _store_product_image(file_storage):
    filename = secure_filename(file_storage.filename)
    if not filename:
        raise ValueError("Invalid image filename!")

    upload_folder = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file_storage.save(file_path)

    cloudinary_url = None
    if _configure_cloudinary():
        try:
            result = cloudinary.uploader.upload(file_path, folder="products")
            cloudinary_url = result.get("secure_url")
        except Exception as exc:
            current_app.logger.warning("Cloudinary upload failed: %s", exc)

    return filename, cloudinary_url


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
    
    # Get orders for the current user
    orders = CustomerOrder.query.filter_by(user_id=user.id).order_by(CustomerOrder.created_at.desc()).all()
    
    # Get cart items count
    cart_count = CartItem.query.filter_by(user_id=user.id).count()
    
    # Calculate order totals (you may need to add total_amount field to CustomerOrder model)
    for order in orders:
        if not hasattr(order, 'total_amount') or order.total_amount is None:
            # Calculate total if not stored
            order.total_amount = sum(item.product.price * item.quantity for item in order.items)
    
    # Get recent orders (last 5)
    recent_orders = orders[:5]

    return render_template(
        "dashboard.html", 
        user=user, 
        products=products,
        orders_count=len(orders),
        recent_orders=recent_orders,
        cart_count=cart_count
    )
    

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
        cloudinary_url = None
        if file and file.filename:
            try:
                filename, cloudinary_url = _store_product_image(file)
            except ValueError as e:
                flash(str(e))
                return redirect(url_for("main.add_product"))
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
            cloudinary_url=cloudinary_url,
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
def update_cart():
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        action = data.get('action')
        if "user_id" not in session:
            return jsonify({'success': False, 'error': 'Login required'}), 401

        cart_item = CartItem.query.filter_by(id=item_id, user_id=session["user_id"]).first_or_404()
        
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

    new_order = CustomerOrder(user_id=user_id, order_status="pending")

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
    return redirect(url_for("main.checkout_success", order_id=new_order.id))


@main.route("/checkout-success/<int:order_id>")
def checkout_success(order_id):
    order = CustomerOrder.query.get_or_404(order_id)
    if "user_id" not in session or order.user_id != session["user_id"]:
        flash("Order lookup failed.")
        return redirect(url_for("main.home"))

    total = sum(item.product.price * item.quantity for item in order.items)
    return render_template("checkout_success.html", order=order, total=total)


@main.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    user_id = session["user_id"]
    orders = CustomerOrder.query.filter_by(user_id=user_id).all()
    return render_template("orders.html", orders=orders)


@main.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id).limit(4).all()
    return render_template("product.html", product=product, related=related)


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
        if image_file and image_file.filename:
            try:
                filename, cloudinary_url = _store_product_image(image_file)
                product.image = filename
                product.cloudinary_url = cloudinary_url
            except ValueError as e:
                flash(str(e))
                return redirect(url_for("main.edit_product", product_id=product_id))
            except Exception as e:
                flash(f"Error saving file: {str(e)}")
                return redirect(url_for("main.edit_product", product_id=product_id))
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
    product_name = product.name

    # Preserve order history by preventing hard delete of products in past orders.
    if OrderItem.query.filter_by(product_id=product.id).first():
        flash("This product cannot be deleted because it exists in customer orders. You can edit it instead.")
        return redirect(url_for("main.admin_products"))

    try:
        # Remove product from active carts first to avoid FK violations on delete.
        CartItem.query.filter_by(product_id=product.id).delete(synchronize_session=False)
        db.session.delete(product)
        db.session.commit()
        flash(f"Product '{product_name}' deleted successfully!")
    except IntegrityError:
        db.session.rollback()
        flash("Unable to delete product due to related records.")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting product: {str(e)}")

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

    # Calculate Revenue
    order_items = OrderItem.query.all()

    revenue = 0
    for item in order_items:
        revenue += item.product.price * item.quantity

    users = User.query.filter(User.id != user.id).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_products=total_products,
        total_categories=total_categories,
        total_orders=total_orders,
        revenue=revenue,
        users=users,
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
    deleted_username = user_to_delete.username
    
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
        
        flash(f"User {deleted_username} has been deleted successfully!")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {str(e)}")
    
    return redirect(url_for("main.admin_users"))  
@main.route('/test-upload', methods=['GET', 'POST'])
def test_upload():
    from flask import request, flash, redirect, url_for, render_template_string
    
    if request.method == 'POST':
        file = request.files.get('image')
        
        if file and file.filename:
            try:
                upload_result = cloudinary.uploader.upload(file, folder="test-uploads")
                cloudinary_url = upload_result['secure_url']
                return f"✅ Success! Image URL: <a href='{cloudinary_url}' target='_blank'>{cloudinary_url}</a><br><br><a href='/test-upload'>Try another</a>"
            except Exception as e:
                return f"❌ Error: {str(e)}"
    
    # Simple HTML form
    return '''
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="image" accept="image/*" required>
        <button type="submit">Test Upload to Cloudinary</button>
    </form>
    '''
