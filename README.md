# Kopito Web Store

Kopito Web Store is a Flask-based e-commerce project with user registration, email verification, product management, cart checkout, and an admin dashboard.

## Features

- User registration and login
- Email verification with code
- Product listing and product details
- Category-based browsing
- Shopping cart and checkout
- Order history
- Admin dashboard for managing products, categories, orders, and users
- Product image upload using local storage and Cloudinary support

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Mail
- MySQL
- Jinja2
- Cloudinary

## Project Structure

```text
Flask-Structured-Application/
├── app/
│   ├── auth/
│   ├── main/
│   ├── static/
│   ├── templates/
│   ├── models.py
│   └── __init__.py
├── run.py
├── requirements.txt
└── README.md
```

## Installation

1. Create a virtual environment
2. Install dependencies
3. Set up environment variables
4. Create the database
5. Run the app

```bash
pip install -r requirements.txt
python run.py
```

## Environment Variables

Create a `.env` file inside `app/` or set these in your environment:

```env
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=your_database_url
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=your_email
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Running the Project

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Admin Access

Users are created as normal users by default. To use admin pages, update the user role in the database to `admin`.

## Notes

- Product images can be stored locally or uploaded to Cloudinary
- Database tables are created automatically when the app starts
