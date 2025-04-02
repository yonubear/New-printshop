from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from enum import Enum

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='created_by', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    address = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='new')  # new, in-progress, completed, cancelled
    due_date = db.Column(db.DateTime)
    total_price = db.Column(db.Float, default=0.0)
    
    # Payment tracking
    payment_status = db.Column(db.String(20), default='unpaid')  # unpaid, partial, paid
    amount_paid = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)  # cash, check, credit_card, etc.
    payment_reference = db.Column(db.String(100), nullable=True)  # check number, transaction ID, etc.
    invoice_number = db.Column(db.String(50), nullable=True)
    payment_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True)
    files = db.relationship('OrderFile', backref='order', lazy=True)
    activities = db.relationship('OrderActivity', backref='order', lazy=True)
    
    @property
    def balance_due(self):
        """Calculate the remaining balance due"""
        return max(0, self.total_price - self.amount_paid)
    
    @property
    def is_paid(self):
        """Check if the order is fully paid"""
        return self.balance_due <= 0
    
    @property
    def payment_progress(self):
        """Calculate payment progress as a percentage"""
        if self.total_price <= 0:
            return 100
        return min(100, int((self.amount_paid / self.total_price) * 100))
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50))  # Stock Keeping Unit
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, in-progress, completed
    
    # Materials required
    materials = db.relationship('ItemMaterial', backref='order_item', lazy=True)
    
    def __repr__(self):
        return f'<OrderItem {self.name}>'

class ItemMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    material_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='pcs')  # pcs, sheets, sq_ft, etc.
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))  # material category: 'paper', 'ink', 'substrate', etc.
    saved_price_id = db.Column(db.Integer, db.ForeignKey('saved_price.id'), nullable=True)  # Link to a saved price if applicable
    
    # Relationship to SavedPrice
    saved_price = db.relationship('SavedPrice', backref='used_in_items', lazy=True, foreign_keys=[saved_price_id])
    
    def __repr__(self):
        return f'<ItemMaterial {self.material_name}>'

class OrderFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # proof, artwork, reference, etc.
    file_path = db.Column(db.String(500))  # Path in Nextcloud
    file_size = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Proof approval fields
    approval_token = db.Column(db.String(100), unique=True, nullable=True)
    approval_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approval_date = db.Column(db.DateTime, nullable=True)
    approval_comment = db.Column(db.Text, nullable=True)
    proof_sent_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<OrderFile {self.original_filename}>'

class OrderActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50))  # status_change, comment, file_upload, etc.
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activities')
    
    def __repr__(self):
        return f'<OrderActivity {self.activity_type}>'
        
class SavedPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50))  # Stock Keeping Unit
    category = db.Column(db.String(50), nullable=False)  # 'paper', 'print_job', 'material', etc.
    cost_price = db.Column(db.Float, default=0.0)  # Cost price (what we pay)
    price = db.Column(db.Float, nullable=False)  # Retail price (what customer pays)
    unit = db.Column(db.String(20), default='each')  # 'each', 'sheet', 'sqft', etc.
    is_template = db.Column(db.Boolean, default=False)  # True for preconfigured job templates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with materials
    materials = db.relationship('SavedPriceMaterial', backref='saved_price', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<SavedPrice {self.name}: ${self.price} per {self.unit}>'

class SavedPriceMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    saved_price_id = db.Column(db.Integer, db.ForeignKey('saved_price.id'), nullable=False)
    material_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='pcs')  # pcs, sheets, sq_ft, etc.
    cost_price = db.Column(db.Float, default=0.0)  # Optional cost price for this material
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))  # material category: 'paper', 'ink', 'substrate', etc.
    
    def __repr__(self):
        return f'<SavedPriceMaterial {self.material_name}: {self.quantity} {self.unit}>'


# Quote Models for custom quoting feature
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, sent, accepted, declined, expired
    valid_until = db.Column(db.DateTime)
    total_price = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade="all, delete-orphan")
    customer = db.relationship('Customer', backref='quotes')
    created_by = db.relationship('User', backref='quotes')
    
    def __repr__(self):
        return f'<Quote {self.quote_number}>'


class QuoteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50))
    
    # Product type
    product_type = db.Column(db.String(50), default='print_job')  # 'print_job', 'booklet', etc.
    
    # Booklet-specific fields
    page_count = db.Column(db.Integer)  # For booklets - total number of pages
    cover_paper_type = db.Column(db.String(100))  # For booklets - cover paper type
    binding_type = db.Column(db.String(50))  # 'saddle_stitch', 'perfect_bound', etc.
    cover_printing = db.Column(db.String(20))  # '4/4', '4/0', etc.
    self_cover = db.Column(db.Boolean, default=False)  # Whether to use same paper for cover
    
    # Print specifications
    size = db.Column(db.String(50))  # e.g., "8.5x11", "11x17", "Custom"
    custom_width = db.Column(db.Float)  # For custom sizes, in inches
    custom_height = db.Column(db.Float)  # For custom sizes, in inches
    finish_size = db.Column(db.String(50))  # Finished size after cutting, e.g., "8.5x11", "5.5x8.5"
    color_type = db.Column(db.String(20))  # "Full Color", "Black & White", "Spot Color"
    sides = db.Column(db.String(20))  # "Single-sided", "Double-sided"
    paper_type = db.Column(db.String(100))  # Paper description
    paper_weight = db.Column(db.String(50))  # Paper weight, e.g., "20#", "80#", "100#"
    
    # Finishing options (comma-separated list of finishing processes)
    finishing_options = db.Column(db.Text)  # "Lamination, Binding, Cutting, Folding"
    
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    
    # Additional options as JSON
    options = db.Column(db.Text)  # JSON string of additional options
    
    def __repr__(self):
        return f'<QuoteItem {self.name}>'


class FinishingOption(db.Model):
    """Pre-defined finishing options and their prices"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # "Binding", "Lamination", "Folding", etc.
    base_price = db.Column(db.Float, default=0.0)  # Starting price
    price_per_piece = db.Column(db.Float, default=0.0)  # Additional price per piece
    price_per_sqft = db.Column(db.Float, default=0.0)  # For large format options
    minimum_price = db.Column(db.Float, default=0.0)  # Minimum charge
    
    def __repr__(self):
        return f'<FinishingOption {self.name}>'


class PaperOption(db.Model):
    """Pre-defined paper types and their prices"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # "Bond", "Cover", "Card Stock", etc.
    weight = db.Column(db.String(20))  # "20#", "80#", "100#", etc.
    size = db.Column(db.String(20))  # "Letter", "Legal", "Tabloid", etc.
    color = db.Column(db.String(50))  # "White", "Colored", etc.
    price_per_sheet = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<PaperOption {self.name} {self.weight}>'


class PrintPricing(db.Model):
    """Pricing configuration for printing (per side)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    paper_size = db.Column(db.String(50))  # "Letter", "Legal", "Tabloid", etc.
    color_type = db.Column(db.String(50))  # "Full Color", "Black & White", "Spot Color"
    price_per_side = db.Column(db.Float, default=0.0)  # Retail price per side
    cost_per_side = db.Column(db.Float, default=0.0)   # Cost price per side (what we pay)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PrintPricing {self.name}: {self.paper_size} {self.color_type}>'
