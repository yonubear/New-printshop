import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from email_service import init_email


# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# configure the database
if os.environ.get("DATABASE_URL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
else:
    # Use the instance folder for SQLite database by default
    db_path = os.path.join(app.instance_path, 'printshop.db')
    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Nextcloud configuration
app.config["NEXTCLOUD_URL"] = os.environ.get("NEXTCLOUD_URL", "")
app.config["NEXTCLOUD_USERNAME"] = os.environ.get("NEXTCLOUD_USERNAME", "")
app.config["NEXTCLOUD_PASSWORD"] = os.environ.get("NEXTCLOUD_PASSWORD", "")
app.config["NEXTCLOUD_FOLDER"] = os.environ.get("NEXTCLOUD_FOLDER", "print_orders")

# Set base URL for link generation
app.config["BASE_URL"] = os.environ.get("BASE_URL", "http://localhost:5000")

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize email service
init_email(app)

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    
    # Create database tables
    db.create_all()
    
    # Import and register routes
    import routes

# Setup login manager loader
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
