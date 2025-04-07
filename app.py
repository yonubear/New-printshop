import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf.csrf import CSRFProtect
from email_service import init_email
import markupsafe


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
    # Create instance directory if it doesn't exist
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

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

# Custom Jinja2 filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    if not text:
        return ""
    return markupsafe.Markup(text.replace('\n', '<br>'))

# Initialize email service
init_email(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    import models
    
    # Create database tables
    db.create_all()
    
    # Import and register routes
    import routes
    import routes_addon  # Import additional routes for QR code tracking
    import routes_preview  # Import interactive print preview routes
    import routes_customer_pricing  # Import customer-specific pricing routes
    
    # Import and register basic pickup routes
    from routes_pickup import basic_pickup_bp
    app.register_blueprint(basic_pickup_bp)
