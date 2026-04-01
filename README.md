# Flask Store & Admin Dashboard

Flask-based storefront with email-verified sign-up, MySQL persistence, cart/checkout flows, and an admin console for products, categories, orders, and users.

## Key Features
- Email-verified registration (Flask-Mail) with hashed passwords.
- Session login/logout and role-based access (`user` vs `admin`).
- Catalog with categories, product images, and detail pages.
- Cart with quantity updates, checkout, order history, and status updates.
- Admin dashboard metrics plus CRUD for products, categories, orders, and users.
- Responsive Jinja templates with custom CSS/JS in `app/static`.

## Tech Stack
- Python 3.10+, Flask, Jinja2, Flask-SQLAlchemy, Flask-Mail, PyMySQL, Werkzeug.
- MySQL 8.x (default DB name: `flask_authentication`).

## Project Layout
C:/Users/Hp 840 g3/PycharmProjects/Student_Management_System/Student_Mangement_System/Structured_Flask/Flask-Structured-Application/
├── run.py
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth/routes.py
│   ├── main/routes.py
│   ├── static/...
│   └── templates/...
└── .git/

## Prerequisites
- Python 3.10 or newer
- MySQL server (user able to create the `flask_authentication` schema)
- SMTP credentials (TLS on port 587; e.g., Gmail app password)

## Setup (local)
1) Clone the repo and `cd` into the path above.
2) Virtualenv: `python -m venv .venv && .\.venv\Scripts\activate`
3) Install deps: `pip install Flask Flask-SQLAlchemy Flask-Mail PyMySQL python-dotenv`
4) Configure secrets (prefer environment variables):
   - `SECRET_KEY`
   - `DATABASE_URL` (e.g., `mysql+pymysql://user:pass@host/dbname`)
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
   The current defaults live in the app factory; adjust or load them from env before running.
5) Create the database (or point `DATABASE_URL` to an existing one):
   `CREATE DATABASE flask_authentication CHARACTER SET utf8mb4;`
6) Start the app (tables auto-create on first run):
   `python "C:/Users/Hp 840 g3/PycharmProjects/Student_Management_System/Student_Mangement_System/Structured_Flask/Flask-Structured-Application/run.py"`
7) Open http://localhost:5000

## Roles and Admin Access
- New users default to role `user`. Promote an account in MySQL:
  `UPDATE user SET role='admin' WHERE email='<your email>';`
- Admin-only areas: dashboard, products, categories, orders, users.

## Email Verification
- Registration sends a 6-digit code via SMTP; verification state is stored in the session.
- For Gmail, create an app password and use TLS on port 587.

## File Uploads
- Product images save to `app/static/uploads`; the folder is created if missing. Ensure the runtime user can write there.

## Helpful Commands
- Flask shell for quick seeding:
  `flask --app "C:/Users/Hp 840 g3/PycharmProjects/Student_Management_System/Student_Mangement_System/Structured_Flask/Flask-Structured-Application/run.py" shell`
- Capture dependencies:
  `pip freeze > requirements.txt`

## Production Checklist
- Replace hard-coded secrets with environment variables; disable `debug=True`.
- Run behind a production WSGI server (gunicorn/uwsgi) and a reverse proxy.
- Use managed MySQL and SMTP; rotate strong passwords.
- Serve `app/static/uploads` via your web server and enforce upload size limits.

_Last updated: 2026-04-01_
