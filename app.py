import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
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
    # Use SQLite database in the instance directory
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/printshop.db"

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
