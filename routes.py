import os
import uuid
import logging
import functools
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort, g, Response, session
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app import app, db
from models import User, Customer, Order, OrderItem, ItemMaterial, OrderFile, OrderActivity, SavedPrice, SavedPriceMaterial, Quote, QuoteItem, QuoteItemMaterial, FinishingOption, PaperOption, PrintPricing
from nextcloud_client import NextcloudClient
from pdf_generator import generate_order_form, generate_pull_sheet, generate_quote_pdf, generate_pickup_receipt, generate_qr_code
from email_service import send_proof_approval_email
from flask_wtf.csrf import CSRFProtect
import io
import qrcode
from PIL import Image as PILImage

# Enable more detailed logging
app.logger.setLevel(logging.DEBUG)

# Verify imports
app.logger.debug("Imports completed successfully")
app.logger.debug(f"Quote model imported: {Quote.__name__}")
app.logger.debug(f"QuoteItem model imported: {QuoteItem.__name__}")
app.logger.debug(f"QuoteItemMaterial model imported: {QuoteItemMaterial.__name__}")

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Define routes that don't need CSRF protection
@app.before_request
def csrf_exempt_routes():
    if request.path.startswith('/track/') or request.path.startswith('/order/qrcode/'):
        csrf.exempt(request.endpoint)

# Login required decorator
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Initialize Nextcloud client if configs are available
if app.config['NEXTCLOUD_URL'] and app.config['NEXTCLOUD_USERNAME'] and app.config['NEXTCLOUD_PASSWORD']:
    # Check if username is in email format - some Nextcloud instances don't handle this properly
    username = app.config['NEXTCLOUD_USERNAME']
    if '@' in username:
        # Try to use the username without the email domain first
        username_without_domain = username.split('@')[0]
        app.logger.info(f"Detected email format username. Will try username: {username_without_domain}")
        username = username_without_domain  # Use the modified username
        
    nextcloud = NextcloudClient(
        app.config['NEXTCLOUD_URL'],
        username,  # Use the possibly modified username
        app.config['NEXTCLOUD_PASSWORD'],
        app.config['NEXTCLOUD_FOLDER']
    )
else:
    # Create dummy client that will log errors instead of failing
    class DummyNextcloudClient:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            
        def upload_file(self, file_obj, file_path):
            self.logger.error("Nextcloud not configured. File upload failed.")
            return False
            
        def download_file(self, file_path):
            self.logger.error("Nextcloud not configured. File download failed.")
            return None
            
        def delete_file(self, file_path):
            self.logger.error("Nextcloud not configured. File deletion failed.")
            return False
            
        def list_files(self, folder_path=""):
            self.logger.error("Nextcloud not configured. Cannot list files.")
            return []
            
        def get_preview_url(self, file_path):
            self.logger.error("Nextcloud not configured. Cannot get preview URL.")
            return None
    
    nextcloud = DummyNextcloudClient()

# Define current_user as a proxy to g.user
class CurrentUser:
    @property
    def id(self):
        return g.user.id if g.user else None
    
    @property
    def is_authenticated(self):
        return g.user is not None

# Create a global instance
current_user = CurrentUser()

# Setup default admin user for all requests (since we've removed authentication)
@app.before_request
def load_logged_in_user():
    # Check if user is logged in
    user_id = session.get('user_id')
    if user_id:
        g.user = User.query.get(user_id)
    else:
        g.user = None

    # Create default admin user if no users exist
    if User.query.count() == 0:
        default_admin = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        default_admin.set_password("password123")
        db.session.add(default_admin)
        db.session.commit()
        app.logger.info("Created default admin user")

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    from flask_wtf import FlaskForm
    from werkzeug.security import check_password_hash
    from wtforms import StringField, PasswordField, SubmitField
    from wtforms.validators import DataRequired
    
    # Create login form with required fields
    class LoginForm(FlaskForm):
        username = StringField('Username', validators=[DataRequired()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Log In')
    
    form = LoginForm()
    
    # Check if already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST' and form.validate_on_submit():
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            
            # Check if there's a next URL to redirect to
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password', 'danger')
    
    return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Dashboard route
@app.route('/')
@login_required
def dashboard():
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get orders by status
    new_orders = Order.query.filter_by(status='new').count()
    in_progress_orders = Order.query.filter_by(status='in-progress').count()
    completed_orders = Order.query.filter_by(status='completed').count()
    
    # Get active quotes (draft, sent, accepted status)
    active_quotes = Quote.query.filter(Quote.status.in_(['draft', 'sent', 'accepted'])).count()
    
    return render_template('dashboard.html',
                           recent_orders=recent_orders,
                           new_orders=new_orders,
                           in_progress_orders=in_progress_orders,
                           completed_orders=completed_orders,
                           active_quotes=active_quotes)

# Customer routes
@app.route('/customers')
@login_required
def customers_index():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/index.html', customers=customers)

@app.route('/customers/create', methods=['GET', 'POST'])
@login_required
def customers_create():
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class CustomerForm(FlaskForm):
        pass
        
    form = CustomerForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        address = request.form.get('address')
        notes = request.form.get('notes')
        discount_percentage = request.form.get('discount_percentage', '0')
        
        # Convert discount percentage to float
        try:
            discount_percentage = float(discount_percentage)
        except (ValueError, TypeError):
            discount_percentage = 0.0
            
        # Ensure discount is between 0 and 100
        discount_percentage = max(0, min(100, discount_percentage))
        
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            company=company,
            address=address,
            notes=notes,
            discount_percentage=discount_percentage
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Customer {name} created successfully', 'success')
        return redirect(url_for('customers_index'))
    
    return render_template('customers/create.html', form=form)

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def customers_edit(id):
    from flask_wtf import FlaskForm
    
    customer = Customer.query.get_or_404(id)
    
    # Create a simple form for CSRF protection
    class CustomerForm(FlaskForm):
        pass
        
    form = CustomerForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.company = request.form.get('company')
        customer.address = request.form.get('address')
        customer.notes = request.form.get('notes')
        
        # Handle the discount percentage
        discount_percentage = request.form.get('discount_percentage', '0')
        
        # Convert discount percentage to float
        try:
            discount_percentage = float(discount_percentage)
        except (ValueError, TypeError):
            discount_percentage = 0.0
            
        # Ensure discount is between 0 and 100
        discount_percentage = max(0, min(100, discount_percentage))
        customer.discount_percentage = discount_percentage
        
        db.session.commit()
        
        flash(f'Customer {customer.name} updated successfully', 'success')
        return redirect(url_for('customers_index'))
    
    return render_template('customers/edit.html', customer=customer, form=form)

# Order routes
@app.route('/orders')
@login_required
def orders_index():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.created_at.desc()).all()
    
    return render_template('orders/index.html', orders=orders, current_filter=status_filter)

@app.route('/orders/create', methods=['GET', 'POST'])
@login_required
def orders_create():
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class OrderForm(FlaskForm):
        pass
    
    form = OrderForm()
    customers = Customer.query.order_by(Customer.name).all()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Get custom order number or generate a unique one
        custom_order_number = request.form.get('order_number')
        
        if custom_order_number and custom_order_number.strip():
            order_number = custom_order_number.strip()
            # Check if this order number already exists
            existing_order = Order.query.filter_by(order_number=order_number).first()
            if existing_order:
                # Append a unique identifier to make it unique
                order_number = f"{order_number}-{str(uuid.uuid4())[:4].upper()}"
        else:
            # Keep generating until we have a unique order number
            while True:
                # Using shorter UUID (6 chars instead of 8) to fit within the column size
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
                # Check if this order number already exists
                existing_order = Order.query.filter_by(order_number=order_number).first()
                if not existing_order:
                    break
        
        customer_id = request.form.get('customer_id')
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        
        # Parse due date if provided
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            
        order = Order(
            order_number=order_number,
            customer_id=customer_id,
            user_id=current_user.id,
            title=title,
            description=description,
            due_date=due_date,
            status='new'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=order.id,
            user_id=current_user.id,
            activity_type='order_created',
            description=f'Order {order.order_number} created'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Order {order.order_number} created successfully', 'success')
        return redirect(url_for('orders_edit', id=order.id))
    
    return render_template('orders/create.html', customers=customers, form=form)

@app.route('/orders/<int:id>')
@login_required
def orders_view(id):
    order = Order.query.get_or_404(id)
    
    # Ensure the order has a tracking code
    tracking_code = order.get_or_create_tracking_code()
    
    activities = OrderActivity.query.filter_by(order_id=id).order_by(OrderActivity.created_at.desc()).all()
    
    # Get the base URL for the tracking link
    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/track/{tracking_code}"
    
    return render_template('orders/view.html', order=order, activities=activities, tracking_url=tracking_url)

@app.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def orders_edit(id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class OrderEditForm(FlaskForm):
        pass
    
    form = OrderEditForm()
    order = Order.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    
    if request.method == 'POST' and form.validate_on_submit():
        order.customer_id = request.form.get('customer_id')
        order.title = request.form.get('title')
        order.description = request.form.get('description')
        order.status = request.form.get('status')
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            order.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=order.id,
            user_id=current_user.id,
            activity_type='order_updated',
            description=f'Order {order.order_number} updated'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Order {order.order_number} updated successfully', 'success')
        return redirect(url_for('orders_view', id=order.id))
    
    # Get all material type prices for the materials dropdown
    saved_materials = SavedPrice.query.filter(
        (SavedPrice.category == 'material') | 
        (SavedPrice.category == 'paper') |
        (SavedPrice.category == 'substrate') |
        (SavedPrice.category == 'laminate') |
        (SavedPrice.category == 'binding')
    ).order_by(SavedPrice.category, SavedPrice.name).all()
    
    return render_template('orders/edit.html', order=order, customers=customers, saved_materials=saved_materials, form=form)

# Order items routes
@app.route('/orders/<int:order_id>/items/add', methods=['POST'])
@login_required
def order_items_add(order_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class ItemAddForm(FlaskForm):
        pass
    
    form = ItemAddForm()
    order = Order.query.get_or_404(order_id)
    
    if form.validate_on_submit():
        name = request.form.get('name')
        description = request.form.get('description')
        sku = request.form.get('sku')
        quantity = int(request.form.get('quantity', 1))
        unit_price = float(request.form.get('unit_price', 0.0))
        
        # Apply customer discount if present
        customer = Customer.query.get(order.customer_id)
        if customer and customer.discount_percentage > 0:
            discount_multiplier = customer.get_discount_multiplier()
            discounted_unit_price = unit_price * discount_multiplier
            total_price = quantity * discounted_unit_price
            
            # Log the discount for debugging
            print(f"DEBUG: Applied customer discount: {customer.discount_percentage}% - Original: {unit_price} -> Discounted: {discounted_unit_price}")
        else:
            total_price = quantity * unit_price
        
        item = OrderItem(
            order_id=order.id,
            name=name,
            description=description,
            sku=sku,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        
        db.session.add(item)
        db.session.flush()  # To get the item ID
        
        # Process materials if any
        material_names = request.form.getlist('material_name[]')
        material_quantities = request.form.getlist('material_quantity[]')
        material_units = request.form.getlist('material_unit[]')
        material_notes = request.form.getlist('material_notes[]')
        material_categories = request.form.getlist('material_categories[]')
        
        # Add materials if available
        if material_names and len(material_names) > 0:
            for i in range(len(material_names)):
                if not material_names[i]:
                    continue
                    
                # Try to find a saved price for this material
                saved_price = SavedPrice.query.filter_by(name=material_names[i], 
                    category=(material_categories[i] if i < len(material_categories) else 'other')).first()
                    
                # Create the material item
                material = ItemMaterial(
                    order_item_id=item.id,
                    material_name=material_names[i],
                    quantity=float(material_quantities[i]) if i < len(material_quantities) and material_quantities[i] else 0,
                    unit=material_units[i] if i < len(material_units) and material_units[i] else 'pcs',
                    notes=material_notes[i] if i < len(material_notes) and material_notes[i] else '',
                    category=material_categories[i] if i < len(material_categories) else 'other',
                    saved_price_id=saved_price.id if saved_price else None
                )
                
                # Log material details for debugging
                print(f"DEBUG: Adding material: {material_names[i]}, category: {material_categories[i] if i < len(material_categories) else 'other'}, saved_price: {saved_price.id if saved_price else 'None'}")
                
                db.session.add(material)
        
        # Update order total
        order.total_price = sum(item.total_price for item in order.items) + total_price
        
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=order.id,
            user_id=current_user.id,
            activity_type='item_added',
            description=f'Item "{name}" added to order with {len([m for m in material_names if m])} materials'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Item added to order successfully', 'success')
        return redirect(url_for('orders_edit', id=order.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('orders_edit', id=order.id))

@app.route('/orders/items/<int:item_id>/edit', methods=['POST'])
@login_required
def order_items_edit(item_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class ItemEditForm(FlaskForm):
        pass
    
    form = ItemEditForm()
    item = OrderItem.query.get_or_404(item_id)
    order = item.order
    
    if form.validate_on_submit():
        item.name = request.form.get('name')
        item.description = request.form.get('description')
        item.sku = request.form.get('sku')
        item.quantity = int(request.form.get('quantity', 1))
        item.unit_price = float(request.form.get('unit_price', 0.0))
        
        # Apply customer discount if present
        customer = Customer.query.get(order.customer_id)
        if customer and customer.discount_percentage > 0:
            discount_multiplier = customer.get_discount_multiplier()
            discounted_unit_price = item.unit_price * discount_multiplier
            item.total_price = item.quantity * discounted_unit_price
            
            # Log the discount for debugging
            print(f"DEBUG: Applied customer discount on edit: {customer.discount_percentage}% - Original: {item.unit_price} -> Discounted: {discounted_unit_price}")
        else:
            item.total_price = item.quantity * item.unit_price
            
        item.status = request.form.get('status')
        
        # Update order total
        order.total_price = sum(i.total_price for i in order.items)
        
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=order.id,
            user_id=current_user.id,
            activity_type='item_updated',
            description=f'Item "{item.name}" updated'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Item updated successfully', 'success')
        return redirect(url_for('orders_edit', id=order.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('orders_edit', id=order.id))

@app.route('/orders/items/<int:item_id>/delete', methods=['POST'])
@login_required
def order_items_delete(item_id):
    item = OrderItem.query.get_or_404(item_id)
    order = item.order
    
    item_name = item.name
    
    db.session.delete(item)
    
    # Update order total
    order.total_price = sum(i.total_price for i in order.items if i.id != item_id)
    
    db.session.commit()
    
    # Create activity log
    activity = OrderActivity(
        order_id=order.id,
        user_id=current_user.id,
        activity_type='item_removed',
        description=f'Item "{item_name}" removed from order'
    )
    db.session.add(activity)
    db.session.commit()
    
    flash(f'Item removed from order successfully', 'success')
    return redirect(url_for('orders_edit', id=order.id))

# Materials routes
@app.route('/orders/items/<int:item_id>/materials/add', methods=['POST'])
@login_required
def item_materials_add(item_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class MaterialAddForm(FlaskForm):
        pass
    
    form = MaterialAddForm()
    item = OrderItem.query.get_or_404(item_id)
    
    if form.validate_on_submit():
        # Check if we're adding from a saved material or manually
        saved_material_id = request.form.get('saved_material_id')
        
        if saved_material_id and saved_material_id != 'custom':
            # Adding from saved material
            saved_price = SavedPrice.query.get_or_404(int(saved_material_id))
            material_name = saved_price.name
            category = saved_price.category
            unit = saved_price.unit
            quantity = float(request.form.get('quantity', 0.0))
            notes = request.form.get('notes')
            saved_price_id = saved_price.id
        else:
            # Manual entry
            material_name = request.form.get('material_name')
            quantity = float(request.form.get('quantity', 0.0))
            unit = request.form.get('unit')
            notes = request.form.get('notes')
            
            # Try to find a saved price for this material
            category = request.form.get('category', 'other')
            saved_price = SavedPrice.query.filter_by(name=material_name, category=category).first()
            saved_price_id = saved_price.id if saved_price else None
        
        material = ItemMaterial(
            order_item_id=item.id,
            material_name=material_name,
            quantity=quantity,
            unit=unit,
            notes=notes,
            category=category,
            saved_price_id=saved_price_id
        )
        
        db.session.add(material)
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=item.order.id,
            user_id=current_user.id,
            activity_type='material_added',
            description=f'Material "{material_name}" added to item "{item.name}"'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Material added to item successfully', 'success')
        return redirect(url_for('orders_edit', id=item.order.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('orders_edit', id=item.order.id))

@app.route('/item-materials/<int:material_id>/edit', methods=['POST'])
@login_required
def item_materials_edit(material_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class MaterialEditForm(FlaskForm):
        pass
    
    form = MaterialEditForm()
    material = ItemMaterial.query.get_or_404(material_id)
    item = OrderItem.query.get_or_404(material.order_item_id)
    
    if form.validate_on_submit():
        # Get the updated values
        quantity = float(request.form.get('quantity', material.quantity))
        notes = request.form.get('notes', material.notes)
        
        # Update the material
        material.quantity = quantity
        material.notes = notes
        
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=item.order.id,
            user_id=current_user.id,
            activity_type='material_updated',
            description=f'Material "{material.material_name}" updated for item "{item.name}"'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Material updated successfully', 'success')
        return redirect(url_for('orders_edit', id=item.order.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('orders_edit', id=item.order.id))

@app.route('/item-materials/<int:material_id>/delete', methods=['POST'])
@login_required
def item_materials_delete(material_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class MaterialDeleteForm(FlaskForm):
        pass
    
    form = MaterialDeleteForm()
    material = ItemMaterial.query.get_or_404(material_id)
    item = OrderItem.query.get_or_404(material.order_item_id)
    material_name = material.material_name
    
    if form.validate_on_submit():
        # Delete the material
        db.session.delete(material)
        
        # Create activity log
        activity = OrderActivity(
            order_id=item.order.id,
            user_id=current_user.id,
            activity_type='material_deleted',
            description=f'Material "{material_name}" removed from item "{item.name}"'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Material removed successfully', 'success')
        return redirect(url_for('orders_edit', id=item.order.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('orders_edit', id=item.order.id))

# File management routes
@app.route('/orders/<int:order_id>/files')
@login_required
def order_files_index(order_id):
    from flask_wtf import FlaskForm
    
    order = Order.query.get_or_404(order_id)
    files = OrderFile.query.filter_by(order_id=order_id).all()
    
    # Create a form instance for CSRF token
    form = FlaskForm()
    
    return render_template('files/index.html', order=order, files=files, form=form)

@app.route('/orders/<int:order_id>/files/upload', methods=['GET', 'POST'])
@login_required
def order_files_upload(order_id):
    from flask_wtf import FlaskForm
    from flask_wtf.file import FileField, FileRequired
    from wtforms import StringField, SubmitField
    
    # Create a form for CSRF protection
    class FileUploadForm(FlaskForm):
        file = FileField('File', validators=[FileRequired()])
        file_type = StringField('File Type')
        submit = SubmitField('Upload File')
    
    order = Order.query.get_or_404(order_id)
    form = FileUploadForm()
    
    if form.validate_on_submit():
        file = request.files.get('file')
        file_type = request.form.get('file_type')
        
        if file and file.filename:
            original_filename = secure_filename(file.filename)
            file_ext = os.path.splitext(original_filename)[1]
            filename = f"{str(uuid.uuid4())}{file_ext}"
            
            # Upload file to Nextcloud
            file_path = f"{order.order_number}/{filename}"
            success = nextcloud.upload_file(file, file_path)
            
            if success:
                # Save file information to database
                order_file = OrderFile(
                    order_id=order.id,
                    filename=filename,
                    original_filename=original_filename,
                    file_type=file_type,
                    file_path=file_path,
                    file_size=len(file.read()),
                    uploaded_by=current_user.id
                )
                
                db.session.add(order_file)
                
                # Create activity log
                activity = OrderActivity(
                    order_id=order.id,
                    user_id=current_user.id,
                    activity_type='file_uploaded',
                    description=f'File "{original_filename}" uploaded as {file_type}'
                )
                db.session.add(activity)
                db.session.commit()
                
                flash(f'File uploaded successfully', 'success')
                return redirect(url_for('order_files_index', order_id=order.id))
            else:
                flash('Failed to upload file to Nextcloud', 'danger')
        else:
            flash('No file selected', 'danger')
    
    return render_template('files/upload.html', order=order, form=form)

@app.route('/files/<int:file_id>/download')
@login_required
def files_download(file_id):
    order_file = OrderFile.query.get_or_404(file_id)
    
    # Download file from Nextcloud
    temp_file_path = nextcloud.download_file(order_file.file_path)
    
    if temp_file_path:
        return send_file(
            temp_file_path,
            download_name=order_file.original_filename,
            as_attachment=True
        )
    else:
        flash('Failed to download file from Nextcloud', 'danger')
        return redirect(url_for('order_files_index', order_id=order_file.order_id))

@app.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
def files_delete(file_id):
    from flask_wtf import FlaskForm
    import logging
    
    # Create a simple form for CSRF protection
    class FileDeleteForm(FlaskForm):
        pass
    
    form = FileDeleteForm()
    order_file = OrderFile.query.get_or_404(file_id)
    order_id = order_file.order_id
    
    # Enhanced logging for debugging
    app.logger.debug(f"Attempting to delete file ID: {file_id}, Path: {order_file.file_path}")
    
    if not form.validate_on_submit():
        app.logger.error(f"CSRF validation failed for file deletion. Form errors: {form.errors}")
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
        return redirect(url_for('order_files_index', order_id=order_id))
    
    try:
        # Set up enhanced logging
        logging.getLogger('nextcloud_client').setLevel(logging.DEBUG)
        
        # Delete file from Nextcloud
        app.logger.debug(f"Calling nextcloud.delete_file({order_file.file_path})")
        success = nextcloud.delete_file(order_file.file_path)
        
        if success:
            app.logger.debug(f"Nextcloud file deletion returned success")
            
            # Create activity log
            activity = OrderActivity(
                order_id=order_id,
                user_id=current_user.id,
                activity_type='file_deleted',
                description=f'File "{order_file.original_filename}" deleted'
            )
            db.session.add(activity)
            
            # Delete file record from database
            db.session.delete(order_file)
            db.session.commit()
            
            flash(f'File deleted successfully', 'success')
        else:
            app.logger.error(f"Nextcloud file deletion failed for {order_file.file_path}")
            flash('Failed to delete file from Nextcloud. Check application logs for details.', 'danger')
    except Exception as e:
        app.logger.error(f"Exception during file deletion: {str(e)}")
        flash(f'An error occurred while deleting the file: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('order_files_index', order_id=order_id))

# PDF generation routes
@app.route('/orders/<int:order_id>/pdf/order-form')
@login_required
def generate_pdf_order_form(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Generate PDF order form
    pdf_file = generate_order_form(order)
    
    # Create activity log
    activity = OrderActivity(
        order_id=order.id,
        user_id=current_user.id,
        activity_type='pdf_generated',
        description='Order form PDF generated'
    )
    db.session.add(activity)
    db.session.commit()
    
    return send_file(
        pdf_file,
        download_name=f"{order.order_number}_order_form.pdf",
        as_attachment=True
    )

@app.route('/orders/<int:order_id>/pdf/pull-sheet')
@login_required
def generate_pdf_pull_sheet(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Generate PDF pull sheet
    pdf_file = generate_pull_sheet(order)
    
    # Create activity log
    activity = OrderActivity(
        order_id=order.id,
        user_id=current_user.id,
        activity_type='pdf_generated',
        description='Material pull sheet PDF generated'
    )
    db.session.add(activity)
    db.session.commit()
    
    return send_file(
        pdf_file,
        download_name=f"{order.order_number}_pull_sheet.pdf",
        as_attachment=True
    )

# Order status update API
@app.route('/api/orders/<int:order_id>/status', methods=['POST'])
@login_required
def api_update_order_status(order_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class OrderStatusUpdateForm(FlaskForm):
        pass
    
    form = OrderStatusUpdateForm()
    order = Order.query.get_or_404(order_id)
    
    # Check if form data was submitted with CSRF token
    if form.validate_on_submit():
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status in ['new', 'in-progress', 'completed', 'cancelled']:
            old_status = order.status
            order.status = new_status
        
            # Create activity log
            activity = OrderActivity(
                order_id=order.id,
                user_id=current_user.id,
                activity_type='status_changed',
                description=f'Order status changed from {old_status} to {new_status}'
            )
            db.session.add(activity)
            db.session.commit()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Invalid status value'}), 400
    else:
        # If CSRF validation failed
        return jsonify({'success': False, 'error': 'CSRF token missing or invalid'}), 403

# File preview route
@app.route('/files/<int:file_id>/preview')
@login_required
def files_preview(file_id):
    order_file = OrderFile.query.get_or_404(file_id)
    
    # Get file preview URL from Nextcloud
    preview_url = nextcloud.get_preview_url(order_file.file_path)
    
    return render_template('files/preview.html', file=order_file, preview_url=preview_url)

# Saved Prices routes
@app.route('/saved-prices')
@login_required
def saved_prices_index():
    categories = SavedPrice.query.with_entities(SavedPrice.category).distinct().all()
    categories = [c[0] for c in categories]
    
    category_filter = request.args.get('category', 'all')
    
    if category_filter == 'all':
        saved_prices = SavedPrice.query.order_by(SavedPrice.category, SavedPrice.name).all()
    else:
        saved_prices = SavedPrice.query.filter_by(category=category_filter).order_by(SavedPrice.name).all()
    
    return render_template('saved_prices/index.html', 
                          saved_prices=saved_prices, 
                          categories=categories, 
                          current_filter=category_filter)

@app.route('/saved-prices/create', methods=['GET', 'POST'])
@login_required
def saved_prices_create():
    # Create a form for CSRF protection
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Extract basic price information
        name = request.form.get('name')
        sku = request.form.get('sku', '')
        description = request.form.get('description', '')
        category = request.form.get('category')
        cost_price = float(request.form.get('cost_price', 0))
        price = float(request.form.get('price', 0))
        unit = request.form.get('unit')
        is_template = 'is_template' in request.form
        
        # Create new saved price record
        new_price = SavedPrice(
            name=name,
            sku=sku,
            description=description,
            category=category,
            cost_price=cost_price,
            price=price,
            unit=unit,
            is_template=is_template
        )
        
        # Add to database
        db.session.add(new_price)
        db.session.commit()
        
        # If this is a template with materials, add material associations
        if is_template:
            # Debug info
            app.logger.debug(f"Processing template materials for new saved price ID: {new_price.id}")
            app.logger.debug(f"Form data: template_material_ids = {request.form.getlist('template_material_ids[]')}")
            app.logger.debug(f"Form data: template_material_quantities = {request.form.getlist('template_material_quantities[]')}")
            app.logger.debug(f"Form data: template_material_is_paper = {request.form.getlist('template_material_is_paper[]')}")
            
            # For template material approach with JavaScript
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            template_material_is_paper = request.form.getlist('template_material_is_paper[]')
            template_material_paper_ids = request.form.getlist('template_material_paper_id[]')
            
            # Process template materials
            for i in range(len(template_material_ids)):
                if not template_material_ids[i]:  # Skip empty entries
                    continue
                
                # Get quantity
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) and template_material_quantities[i] else 1
                
                # Check if this is a paper option
                is_paper = i < len(template_material_is_paper) and template_material_is_paper[i] == 'true'
                
                if is_paper:
                    # This is a paper option, extract the paper ID from the value
                    paper_id_str = template_material_ids[i].replace('paper_', '')
                    paper_id = int(paper_id_str) if paper_id_str.isdigit() else None
                    
                    if paper_id:
                        # Get the paper option from database
                        paper_option = PaperOption.query.get(paper_id)
                        
                        if paper_option:
                            # Format paper name
                            paper_name = f"{paper_option.weight} {paper_option.color} ({paper_option.size})"
                            paper_name = paper_name.replace("  ", " ").strip()
                            
                            # Create material association
                            material = SavedPriceMaterial(
                                saved_price_id=new_price.id,
                                material_name=paper_name,
                                quantity=quantity,
                                unit="sheet",
                                cost_price=paper_option.cost_per_sheet if paper_option.cost_per_sheet else 0.0,
                                notes=f"Linked to paper option ID: {paper_id}",
                                category="paper"
                            )
                            
                            db.session.add(material)
                else:
                    # Regular material
                    try:
                        material_id = int(template_material_ids[i])
                        material_price = SavedPrice.query.get(material_id)
                        
                        if not material_price:
                            continue
                            
                        # Create material association
                        material = SavedPriceMaterial(
                            saved_price_id=new_price.id,
                            material_name=material_price.name,
                            quantity=quantity,
                            unit=material_price.unit,
                            cost_price=material_price.cost_price,
                            notes=f"Linked to material ID: {material_id}",
                            category=material_price.category
                        )
                        
                        db.session.add(material)
                    except ValueError:
                        # If there's an error converting the ID to int, skip this entry
                        continue
            
            db.session.commit()
        
        flash(f'Price item "{name}" created successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
    # Get all material type prices for the materials dropdown
    materials = SavedPrice.query.filter(
        SavedPrice.category == 'material'
    ).order_by(SavedPrice.name).all()
    
    # Get paper options directly from the paper_option table
    paper_options = PaperOption.query.order_by(PaperOption.name).all()
    
    # Combine them into a single list of materials
    for paper in paper_options:
        # Format the paper name for display
        paper_display_name = f"{paper.weight} {paper.color} ({paper.size})"
        paper_display_name = paper_display_name.replace("  ", " ").strip()
        
        # Add a custom attribute to identify this as a paper option
        paper.is_paper_option = True
        paper.display_name = paper_display_name
        
        # Add a unit_price attribute to make it compatible with saved prices
        paper.price = paper.cost_per_sheet * 2 if paper.cost_per_sheet else 0.0
        paper.unit = "sheet"
        paper.category = "paper"
    
    return render_template('saved_prices/create.html', materials=materials, paper_options=paper_options, form=form)

@app.route('/saved-prices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def saved_prices_edit(id):
    saved_price = SavedPrice.query.get_or_404(id)
    
    # Create a form for CSRF protection
    from flask_wtf import FlaskForm
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Update basic information
        saved_price.name = request.form.get('name')
        saved_price.sku = request.form.get('sku', '')
        saved_price.description = request.form.get('description', '')
        saved_price.category = request.form.get('category')
        saved_price.cost_price = float(request.form.get('cost_price', 0))
        saved_price.price = float(request.form.get('price', 0))
        saved_price.unit = request.form.get('unit')
        saved_price.is_template = 'is_template' in request.form
        
        # If it's a template, handle materials
        if saved_price.is_template:
            # Debug info
            app.logger.debug(f"Processing template materials for saved price ID: {saved_price.id}")
            app.logger.debug(f"Form data: template_material_ids = {request.form.getlist('template_material_ids[]')}")
            app.logger.debug(f"Form data: template_material_quantities = {request.form.getlist('template_material_quantities[]')}")
            app.logger.debug(f"Form data: template_material_is_paper = {request.form.getlist('template_material_is_paper[]')}")
            
            # Remove all existing materials
            SavedPriceMaterial.query.filter_by(saved_price_id=id).delete()
            
            # Add new materials from form
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            template_material_is_paper = request.form.getlist('template_material_is_paper[]')
            template_material_paper_ids = request.form.getlist('template_material_paper_id[]')
            
            # Process template materials
            for i in range(len(template_material_ids)):
                if not template_material_ids[i]:  # Skip empty entries
                    continue
                
                # Get quantity
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) and template_material_quantities[i] else 1
                
                # Check if this is a paper option
                is_paper = i < len(template_material_is_paper) and template_material_is_paper[i] == 'true'
                
                if is_paper:
                    # This is a paper option, extract the paper ID from the value
                    paper_id_str = template_material_ids[i].replace('paper_', '')
                    paper_id = int(paper_id_str) if paper_id_str.isdigit() else None
                    
                    if paper_id:
                        # Get the paper option from database
                        paper_option = PaperOption.query.get(paper_id)
                        
                        if paper_option:
                            # Format paper name
                            paper_name = f"{paper_option.weight} {paper_option.color} ({paper_option.size})"
                            paper_name = paper_name.replace("  ", " ").strip()
                            
                            # Create material association
                            material = SavedPriceMaterial(
                                saved_price_id=saved_price.id,
                                material_name=paper_name,
                                quantity=quantity,
                                unit="sheet",
                                cost_price=paper_option.cost_per_sheet if paper_option.cost_per_sheet else 0.0,
                                notes=f"Linked to paper option ID: {paper_id}",
                                category="paper"
                            )
                            
                            db.session.add(material)
                else:
                    # Regular material
                    try:
                        material_id = int(template_material_ids[i])
                        material_price = SavedPrice.query.get(material_id)
                        
                        if not material_price:
                            continue
                            
                        # Create material association
                        material = SavedPriceMaterial(
                            saved_price_id=saved_price.id,
                            material_name=material_price.name,
                            quantity=quantity,
                            unit=material_price.unit,
                            cost_price=material_price.cost_price,
                            notes=f"Linked to material ID: {material_id}",
                            category=material_price.category
                        )
                        
                        db.session.add(material)
                    except ValueError:
                        # If there's an error converting the ID to int, skip this entry
                        continue
        
        # Save changes
        db.session.commit()
        
        flash(f'Price item "{saved_price.name}" updated successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
    # Get all material type prices for the materials dropdown
    materials = SavedPrice.query.filter(
        SavedPrice.category == 'material'
    ).order_by(SavedPrice.name).all()
    
    # Get paper options directly from the paper_option table
    paper_options = PaperOption.query.order_by(PaperOption.name).all()
    
    # Combine them into a single list of materials
    for paper in paper_options:
        # Format the paper name for display
        paper_display_name = f"{paper.weight} {paper.color} ({paper.size})"
        paper_display_name = paper_display_name.replace("  ", " ").strip()
        
        # Add a custom attribute to identify this as a paper option
        paper.is_paper_option = True
        paper.display_name = paper_display_name
        
        # Add a unit_price attribute to make it compatible with saved prices
        paper.price = paper.cost_per_sheet * 2 if paper.cost_per_sheet else 0.0
        paper.unit = "sheet"
        paper.category = "paper"
    
    # Get existing template materials
    template_materials = []
    if saved_price.is_template:
        for tm in saved_price.materials:
            # Check if this material is a paper by looking at notes
            is_paper = 'Linked to paper option ID' in tm.notes if tm.notes else False
            
            if is_paper:
                # Extract the paper ID from the notes
                import re
                paper_id_match = re.search(r'Linked to paper option ID: (\d+)', tm.notes)
                paper_id = int(paper_id_match.group(1)) if paper_id_match else 0
                
                template_materials.append({
                    'material_id': f"paper_{paper_id}",
                    'material_name': tm.material_name,
                    'quantity': tm.quantity,
                    'is_paper': True,
                    'paper_id': paper_id
                })
            else:
                # Try to find the linked material by name
                linked_material = SavedPrice.query.filter_by(name=tm.material_name).first()
                material_id = linked_material.id if linked_material else 0
                
                template_materials.append({
                    'material_id': material_id,
                    'material_name': tm.material_name,
                    'quantity': tm.quantity,
                    'is_paper': False
                })
    
    return render_template('saved_prices/edit.html', 
                          saved_price=saved_price, 
                          materials=materials,
                          paper_options=paper_options,
                          template_materials=template_materials,
                          form=form)

@app.route('/saved-prices/<int:id>/delete', methods=['POST'])
@login_required
def saved_prices_delete(id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class SavedPriceDeleteForm(FlaskForm):
        pass
    
    form = SavedPriceDeleteForm()
    saved_price = SavedPrice.query.get_or_404(id)
    name = saved_price.name
    
    if form.validate_on_submit():
        db.session.delete(saved_price)
        db.session.commit()
        
        flash(f'Price item "{name}" deleted successfully', 'success')
    else:
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
    
    return redirect(url_for('saved_prices_index'))

@app.route('/saved_prices/import', methods=['GET', 'POST'])
@login_required
def saved_prices_import():
    from flask_wtf import FlaskForm
    from flask_wtf.file import FileField, FileRequired, FileAllowed
    from wtforms import SubmitField
    
    # Create form for CSRF protection and file validation
    class ImportForm(FlaskForm):
        excel_file = FileField('Excel File', validators=[
            FileRequired(), 
            FileAllowed(['xlsx', 'xls'], 'Excel files only!')
        ])
        submit = SubmitField('Import')
    
    form = ImportForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        file = form.excel_file.data
        
        if file and allowed_file(file.filename, ['xlsx', 'xls']):
            try:
                # Import data from Excel
                import pandas as pd
                
                # Try to read the file as a comprehensive template first (with multiple sheets)
                try:
                    # Check if the file has multiple sheets
                    xls = pd.ExcelFile(file)
                    sheet_names = xls.sheet_names
                    
                    # Process Paper Options if available
                    if 'Paper Options' in sheet_names:
                        paper_df = pd.read_excel(file, sheet_name='Paper Options')
                        paper_success, paper_error = process_paper_options_import(paper_df)
                        if paper_success > 0:
                            flash(f"Successfully imported {paper_success} paper options.", 'success')
                        if paper_error > 0:
                            flash(f"Failed to import {paper_error} paper options due to errors.", 'warning')
                    
                    # Process Finishing Options if available
                    if 'Finishing Options' in sheet_names:
                        finishing_df = pd.read_excel(file, sheet_name='Finishing Options')
                        finishing_success, finishing_error = process_finishing_options_import(finishing_df)
                        if finishing_success > 0:
                            flash(f"Successfully imported {finishing_success} finishing options.", 'success')
                        if finishing_error > 0:
                            flash(f"Failed to import {finishing_error} finishing options due to errors.", 'warning')
                    
                    # Process Print Pricing if available
                    if 'Print Pricing' in sheet_names:
                        pricing_df = pd.read_excel(file, sheet_name='Print Pricing')
                        pricing_success, pricing_error = process_pricing_import(pricing_df)
                        if pricing_success > 0:
                            flash(f"Successfully imported {pricing_success} pricing configurations.", 'success')
                        if pricing_error > 0:
                            flash(f"Failed to import {pricing_error} pricing configurations due to errors.", 'warning')
                    
                    # Process Saved Prices if available
                    if 'Saved Prices' in sheet_names:
                        prices_df = pd.read_excel(file, sheet_name='Saved Prices')
                        success_count, error_count = process_saved_prices_sheet(prices_df)
                        if success_count > 0:
                            flash(f"Successfully imported {success_count} saved prices.", 'success')
                        if error_count > 0:
                            flash(f"Failed to import {error_count} saved prices due to errors.", 'warning')
                    elif len(sheet_names) == 1:
                        # If there's only one sheet and it's not named, assume it's for saved prices
                        df = pd.read_excel(file)
                        success_count, error_count = process_saved_prices_sheet(df)
                        if success_count > 0:
                            flash(f"Successfully imported {success_count} saved prices.", 'success')
                        if error_count > 0:
                            flash(f"Failed to import {error_count} saved prices due to errors.", 'warning')
                    
                    return redirect(url_for('saved_prices_index'))
                except Exception as e:
                    # If there's an error with the comprehensive import, try the traditional method
                    try:
                        # Read Excel file as a single sheet
                        df = pd.read_excel(file)
                        
                        # Define required columns for saved prices
                        required_columns = ['name', 'category', 'price']
                        
                        # Check if all required columns exist
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        if missing_columns:
                            flash(f"Missing required columns: {', '.join(missing_columns)}. Please check the Excel template.", 'danger')
                            return redirect(request.url)
                        
                        # Process each row as a saved price
                        success_count = 0
                        error_count = 0
                        
                        for index, row in df.iterrows():
                            try:
                                # Create new saved price
                                saved_price = SavedPrice(
                                    name=row['name'],
                                    description=row.get('description', ''),
                                    sku=row.get('sku', ''),
                                    category=row['category'],
                                    cost_price=float(row.get('cost_price', 0)),
                                    price=float(row['price']),
                                    unit=row.get('unit', 'each'),
                                    is_template=bool(row.get('is_template', False))
                                )
                                
                                # Add materials if present
                                if 'materials' in row and row['materials']:
                                    materials_list = str(row['materials']).split(',')
                                    for material_str in materials_list:
                                        parts = material_str.strip().split(':')
                                        if len(parts) >= 2:
                                            material_name = parts[0].strip()
                                            quantity = float(parts[1].strip())
                                            
                                            material = SavedPriceMaterial(
                                                material_name=material_name,
                                                quantity=quantity,
                                                unit=parts[2].strip() if len(parts) > 2 else 'pcs'
                                            )
                                            saved_price.materials.append(material)
                                
                                db.session.add(saved_price)
                                success_count += 1
                            
                            except Exception as e:
                                error_count += 1
                                print(f"Error processing row {index + 2}: {str(e)}")
                        
                        # Commit changes
                        db.session.commit()
                        
                        if error_count > 0:
                            flash(f'Imported {success_count} items successfully with {error_count} errors.', 'warning')
                        else:
                            flash(f'Successfully imported {success_count} items.', 'success')
                        
                        return redirect(url_for('saved_prices_index'))
                    except Exception as e:
                        flash(f'Error processing file: {str(e)}', 'danger')
                        return redirect(request.url)
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('saved_prices/import.html', form=form)


# Helper function to process paper options import
def process_paper_options_import(df):
    """Process a paper options Excel sheet"""
    success_count = 0
    error_count = 0
    
    # Define required columns
    required_columns = ['name', 'category', 'weight', 'size', 'price_per_sheet']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        flash(f"Missing required columns for paper options: {', '.join(missing_columns)}", 'danger')
        return 0, 0
        
    # Process each row
    for index, row in df.iterrows():
        try:
            # Create new paper option
            paper_option = PaperOption(
                name=row['name'],
                description=row.get('description', ''),
                category=row['category'],
                weight=row['weight'],
                size=row['size'],
                color=row.get('color', 'White'),
                price_per_sheet=float(row.get('price_per_sheet', 0.0)),
                cost_per_sheet=float(row.get('cost_per_sheet', 0.0))
            )
            
            db.session.add(paper_option)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error processing paper option row {index + 2}: {str(e)}")
    
    # Commit changes
    db.session.commit()
    
    return success_count, error_count


# Helper function to process finishing options import
def process_finishing_options_import(df):
    """Process a finishing options Excel sheet"""
    success_count = 0
    error_count = 0
    
    # Define required columns
    required_columns = ['name', 'category', 'base_price']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        flash(f"Missing required columns for finishing options: {', '.join(missing_columns)}", 'danger')
        return 0, 0
        
    # Process each row
    for index, row in df.iterrows():
        try:
            # Create new finishing option
            finishing_option = FinishingOption(
                name=row['name'],
                description=row.get('description', ''),
                category=row['category'],
                base_price=float(row.get('base_price', 0.0)),
                price_per_piece=float(row.get('price_per_piece', 0.0)),
                price_per_sqft=float(row.get('price_per_sqft', 0.0)),
                minimum_price=float(row.get('minimum_price', 0.0))
            )
            
            db.session.add(finishing_option)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error processing finishing option row {index + 2}: {str(e)}")
    
    # Commit changes
    db.session.commit()
    
    return success_count, error_count


# Helper function to process print pricing import
def process_pricing_import(df):
    """Process a print pricing Excel sheet"""
    success_count = 0
    error_count = 0
    
    # Define required columns
    required_columns = ['name', 'paper_size', 'color_type', 'price_per_side']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        flash(f"Missing required columns for print pricing: {', '.join(missing_columns)}", 'danger')
        return 0, 0
        
    # Process each row
    for index, row in df.iterrows():
        try:
            # Create new print pricing
            pricing = PrintPricing(
                name=row['name'],
                paper_size=row['paper_size'],
                color_type=row['color_type'],
                price_per_side=float(row.get('price_per_side', 0.0)),
                cost_per_side=float(row.get('cost_per_side', 0.0)),
                notes=row.get('notes', '')
            )
            
            db.session.add(pricing)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"Error processing print pricing row {index + 2}: {str(e)}")
    
    # Commit changes
    db.session.commit()
    
    return success_count, error_count


# Helper function to process saved prices sheet
def process_saved_prices_sheet(df):
    """Process a saved prices Excel sheet"""
    # Define required columns
    required_columns = ['name', 'category', 'price']
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        flash(f"Missing required columns: {', '.join(missing_columns)}. Please check the Excel template.", 'danger')
        return 0, 0
    
    # Process each row
    success_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            # Create new saved price
            saved_price = SavedPrice(
                name=row['name'],
                description=row.get('description', ''),
                sku=row.get('sku', ''),
                category=row['category'],
                cost_price=float(row.get('cost_price', 0)),
                price=float(row['price']),
                unit=row.get('unit', 'each'),
                is_template=bool(row.get('is_template', False))
            )
            
            # Add materials if present
            if 'materials' in row and row['materials']:
                materials_list = str(row['materials']).split(',')
                for material_str in materials_list:
                    parts = material_str.strip().split(':')
                    if len(parts) >= 2:
                        material_name = parts[0].strip()
                        quantity = float(parts[1].strip())
                        
                        material = SavedPriceMaterial(
                            material_name=material_name,
                            quantity=quantity,
                            unit=parts[2].strip() if len(parts) > 2 else 'pcs'
                        )
                        saved_price.materials.append(material)
            
            db.session.add(saved_price)
            success_count += 1
        
        except Exception as e:
            error_count += 1
            print(f"Error processing row {index + 2}: {str(e)}")
    
    # Commit changes
    db.session.commit()
    
    return success_count, error_count

# Helper function for file extensions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
           
@app.route('/saved_prices/download-template')
@login_required
def download_excel_template():
    """Generate and download a sample Excel template for pricing import"""
    import pandas as pd
    import io
    
    # Create sample data
    data = {
        'name': [
            'Business Cards', 
            'Flyer - Letter', 
            'Premium Cardstock', 
            'Lamination - 5mil'
        ],
        'description': [
            '3.5x2 inch, Full Color, 110# Gloss Cover',
            '8.5x11 inch, Full Color, 100# Gloss Text',
            '110# Cover, White',
            '5mil Gloss Lamination'
        ],
        'category': [
            'print_job',
            'print_job',
            'paper',
            'finishing'
        ],
        'sku': [
            'BC-STD',
            'FLY-LTR',
            'STK-110C',
            'LAM-5G'
        ],
        'cost_price': [
            0.05,
            0.15,
            0.10,
            1.00
        ],
        'price': [
            25.00,
            0.75,
            0.25,
            2.50
        ],
        'unit': [
            'pack',
            'each',
            'sheet',
            'sqft'
        ],
        'is_template': [
            True,
            False,
            False,
            False
        ],
        'materials': [
            'Cardstock:25:sheets, Ink:0.5:ml',
            '',
            '',
            ''
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to BytesIO (in-memory file)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        download_name='pricing_template.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/saved_prices/download-comprehensive-template')
@login_required
def download_comprehensive_template():
    """Generate and download a comprehensive Excel template with multiple tabs"""
    import os
    
    # Check if the pre-generated file exists
    if os.path.exists('comprehensive_import_template.xlsx'):
        # Use the pre-generated file to avoid potential timeout issues
        return send_file(
            'comprehensive_import_template.xlsx',
            download_name='comprehensive_import_template.xlsx',
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    
    # If the file doesn't exist, generate it in memory
    # Import necessary libraries and functions
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from generate_comprehensive_template import (
        create_paper_options_sheet,
        create_finishing_options_sheet,
        create_print_pricing_sheet,
        create_saved_prices_sheet,
        create_header_style,
        auto_adjust_columns,
        add_info_header
    )
    import pandas as pd
    import io
    
    # Create an in-memory Excel file
    output = io.BytesIO()
    
    # Create dataframes for each sheet
    paper_df = create_paper_options_sheet()
    finishing_df = create_finishing_options_sheet()
    printing_df = create_print_pricing_sheet()
    saved_prices_df = create_saved_prices_sheet()
    
    # Write to the in-memory Excel file
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write each dataframe to a separate sheet
        paper_df.to_excel(writer, sheet_name='Paper Options', index=False)
        finishing_df.to_excel(writer, sheet_name='Finishing Options', index=False)
        printing_df.to_excel(writer, sheet_name='Print Pricing', index=False)
        saved_prices_df.to_excel(writer, sheet_name='Saved Prices', index=False)
        
        # Get workbook and apply formatting
        workbook = writer.book
        
        # Format Paper Options sheet
        paper_sheet = workbook['Paper Options']
        create_header_style(paper_sheet)
        auto_adjust_columns(paper_sheet)
        add_info_header(
            paper_sheet, 
            "Paper Options Import Template",
            "Add paper types with their specifications. These will be available for selection in order and quote forms."
        )
        
        # Format Finishing Options sheet
        finishing_sheet = workbook['Finishing Options']
        create_header_style(finishing_sheet)
        auto_adjust_columns(finishing_sheet)
        add_info_header(
            finishing_sheet, 
            "Finishing Options Import Template",
            "Add finishing options like lamination, binding, etc. These will be available as add-ons for orders and quotes."
        )
        
        # Format Print Pricing sheet
        printing_sheet = workbook['Print Pricing']
        create_header_style(printing_sheet)
        auto_adjust_columns(printing_sheet)
        add_info_header(
            printing_sheet, 
            "Print Pricing Import Template",
            "Add pricing configurations for different print options (per side). These will be used for automatic price calculations."
        )
        
        # Format Saved Prices sheet
        saved_prices_sheet = workbook['Saved Prices']
        create_header_style(saved_prices_sheet)
        auto_adjust_columns(saved_prices_sheet)
        add_info_header(
            saved_prices_sheet, 
            "Saved Prices Import Template",
            "Add common print jobs, materials, and services with their prices. For materials, use format: 'Name:Quantity:Unit, Name2:Quantity2:Unit2'"
        )
    
    # Reset the pointer to the beginning of the file
    output.seek(0)
    
    return send_file(
        output,
        download_name='comprehensive_import_template.xlsx',
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# API endpoints for quote calculator

# API to get paper options for the quote calculator
@app.route('/api/paper-options', methods=['GET'])
def api_paper_options():
    """Return all paper options as JSON for the price calculator"""
    # Debug output
    app.logger.debug("Paper options API requested")
    
    # Query all paper options or filter by category if provided
    paper_type = request.args.get('type')
    
    if paper_type:
        app.logger.debug(f"Filtering by paper type: {paper_type}")
        options = PaperOption.query.filter_by(category=paper_type).all()
    else:
        options = PaperOption.query.all()
    
    app.logger.debug(f"Found {len(options)} paper options")
    
    # Convert to JSON
    result = []
    for option in options:
        result.append({
            'id': option.id,
            'name': option.name,
            'size': option.size,
            'type': option.category,  # Use category field 
            'category': option.category,  # Add explicit category field
            'weight': option.weight,
            'color': option.color,
            'price_per_sheet': float(option.price_per_sheet) if option.price_per_sheet else 0.0,
            'cost_per_sheet': float(option.cost_per_sheet) if option.cost_per_sheet else 0.0,
            'width': float(option.width) if option.width else 0.0,
            'height': float(option.height) if option.height else 0.0,
            'is_roll': bool(option.is_roll),
            'price_per_sqft': float(option.price_per_sqft) if option.price_per_sqft else 0.0,
            'cost_per_sqft': float(option.cost_per_sqft) if option.cost_per_sqft else 0.0,
            'pricing_method': option.pricing_method
        })
    
    app.logger.debug(f"Returning {len(result)} paper options")
    return jsonify(result)

# API to get print pricing options - public API
@app.route('/api/print-pricing', methods=['GET'])
def api_print_pricing():
    """Return all print pricing options as JSON for the price calculator"""
    # Debug output
    app.logger.debug("Print pricing API requested")
    
    # Query all print pricing or filter by color if provided
    color_type = request.args.get('color')
    
    if color_type:
        app.logger.debug(f"Filtering by color type: {color_type}")
        pricing = PrintPricing.query.filter_by(color_type=color_type).all()
    else:
        pricing = PrintPricing.query.all()
    
    app.logger.debug(f"Found {len(pricing)} print pricing options")
    
    # Convert to JSON
    result = []
    for price in pricing:
        price_data = {
            'id': price.id,
            'name': price.name,
            'paper_size': price.paper_size,
            'color': price.color_type,
            'paper_type': price.paper_type if hasattr(price, 'paper_type') else None,
            'paper_category': price.paper_type if hasattr(price, 'paper_type') else None,  # Add explicit paper_category field
            'per_page_price': float(price.price_per_side) if price.price_per_side else 0.0,
            'per_page_cost': float(price.cost_per_side) if price.cost_per_side else 0.0,
            'price_per_sqft': float(price.price_per_sqft) if hasattr(price, 'price_per_sqft') and price.price_per_sqft else 0.0,
            'cost_per_sqft': float(price.cost_per_sqft) if hasattr(price, 'cost_per_sqft') and price.cost_per_sqft else 0.0,
            'pricing_method': price.pricing_method if hasattr(price, 'pricing_method') else 'side',
            'base_price': 0.50,  # Base setup charge
            'duplex': price.paper_size != 'Roll Media' # Assume duplex printing for everything except roll media
        }
        result.append(price_data)
        app.logger.debug(f"Added pricing option: {price.name} (Color: {price.color_type}, Size: {price.paper_size})")
    
    app.logger.debug(f"Returning {len(result)} print pricing options")
    return jsonify(result)

# Diagnostic page for API testing
@app.route('/api-test')
def api_test():
    """Render a diagnostic page for testing API endpoints"""
    return render_template('api_test.html')

# API to get finishing option categories - public API
@app.route('/api/finishing-categories', methods=['GET'])
def api_finishing_categories():
    """Return all unique finishing option categories as JSON"""
    app.logger.debug("API request for finishing categories received")
    # Get all finishing options from database
    options = FinishingOption.query.all()
    app.logger.debug(f"Found {len(options)} finishing options in database")
    
    # Extract unique categories
    categories = set()
    for option in options:
        if option.category:
            categories.add(option.category)
            app.logger.debug(f"Added category: {option.category}")
    
    # Convert to sorted list
    category_list = sorted(list(categories))
    app.logger.debug(f"Returning {len(category_list)} categories: {category_list}")
    
    return jsonify(category_list)

# API to get finishing options for the quote calculator - public API
@app.route('/api/finishing-options', methods=['GET'])
def api_finishing_options():
    """Return all finishing options as JSON for the price calculator"""
    app.logger.debug("API request for finishing options received")
    # Query all finishing options or filter by category if provided
    category = request.args.get('category')
    app.logger.debug(f"Finishing options category filter: {category}")
    
    if category:
        options = FinishingOption.query.filter_by(category=category).all()
        app.logger.debug(f"Found {len(options)} finishing options for category '{category}'")
    else:
        options = FinishingOption.query.all()
        app.logger.debug(f"Found {len(options)} finishing options across all categories")
    
    # Convert to JSON
    result = []
    for option in options:
        option_data = {
            'id': option.id,
            'name': option.name,
            'description': option.description,
            'category': option.category,
            'base_price': float(option.base_price) if option.base_price else 0.0,
            'price_per_piece': float(option.price_per_piece) if option.price_per_piece else 0.0,
            'price_per_sqft': float(option.price_per_sqft) if option.price_per_sqft else 0.0,
            'minimum_price': float(option.minimum_price) if option.minimum_price else 0.0
        }
        result.append(option_data)
        app.logger.debug(f"Added option: {option.name} ({option.category})")
    
    app.logger.debug(f"Returning {len(result)} finishing options")
    return jsonify(result)

# API to retrieve saved prices for order form
@app.route('/api/saved-prices', methods=['GET'])
def api_saved_prices():
    category = request.args.get('category')
    include_materials = request.args.get('include_materials', 'false').lower() == 'true'
    
    if category:
        prices = SavedPrice.query.filter_by(category=category).order_by(SavedPrice.name).all()
    else:
        prices = SavedPrice.query.order_by(SavedPrice.category, SavedPrice.name).all()
    
    # Convert to JSON serializable format
    result = []
    for price in prices:
        price_data = {
            'id': price.id,
            'name': price.name,
            'description': price.description,
            'sku': price.sku,
            'category': price.category,
            'cost_price': price.cost_price,
            'price': price.price,
            'unit': price.unit,
            'is_template': price.is_template
        }
        
        # Include materials if requested and this is a template
        if include_materials and price.is_template:
            price_data['materials'] = []
            for material in price.materials:
                price_data['materials'].append({
                    'id': material.id,
                    'material_name': material.material_name,
                    'quantity': material.quantity,
                    'unit': material.unit,
                    'cost_price': material.cost_price,
                    'notes': material.notes,
                    'category': material.category or 'other'
                })
                
        result.append(price_data)
    
    return jsonify(result)

# API to retrieve saved materials by category
@app.route('/api/materials', methods=['GET'])
def api_materials():
    category = request.args.get('category', 'all')
    
    # Query saved prices where category is 'material' or the specific category
    if category != 'all':
        materials = SavedPrice.query.filter_by(category='material').filter(
            SavedPrice.name.like(f'%{category}%') | 
            SavedPrice.description.like(f'%{category}%')
        ).order_by(SavedPrice.name).all()
    else:
        materials = SavedPrice.query.filter_by(category='material').order_by(SavedPrice.name).all()
    
    # Convert to JSON serializable format
    result = []
    for material in materials:
        result.append({
            'id': material.id,
            'name': material.name,
            'description': material.description,
            'sku': material.sku,
            'cost_price': material.cost_price,
            'price': material.price,
            'unit': material.unit
        })
    
    return jsonify(result)

# Quote routes
@app.route('/quotes')
@login_required
def quotes_index():
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        quotes = Quote.query.order_by(Quote.created_at.desc()).all()
    else:
        quotes = Quote.query.filter_by(status=status_filter).order_by(Quote.created_at.desc()).all()
    
    return render_template('quotes/index.html', quotes=quotes, current_filter=status_filter)

@app.route('/quotes/create', methods=['GET', 'POST'])
@login_required
def quotes_create():
    from flask_wtf import FlaskForm
    from wtforms import HiddenField, StringField, TextAreaField, SelectField, DateField
    
    # Create a form with all needed fields
    class QuoteForm(FlaskForm):
        customer_id_hidden = HiddenField('Customer ID')
        quote_number = StringField('Quote Number')
        title = StringField('Title')
        description = TextAreaField('Description')
        status = SelectField('Status', choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ])
        valid_until = DateField('Valid Until', format='%Y-%m-%d', validators=[])
    
    # Create a form for quote items too
    class QuoteItemForm(FlaskForm):
        pass
    
    form = QuoteForm()
    item_form = QuoteItemForm()
    customers = Customer.query.order_by(Customer.name).all()
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    if request.method == 'POST' and form.validate_on_submit():
        app.logger.info("Starting quote creation process")
        # Get custom quote number or generate a unique one
        custom_quote_number = request.form.get('quote_number')
        
        if custom_quote_number and custom_quote_number.strip():
            quote_number = custom_quote_number.strip()
            # Check if this quote number already exists
            existing_quote = Quote.query.filter_by(quote_number=quote_number).first()
            if existing_quote:
                # Append a unique identifier to make it unique
                quote_number = f"{quote_number}-{str(uuid.uuid4())[:4].upper()}"
                app.logger.info(f"Modified duplicate quote number to: {quote_number}")
        else:
            # Keep generating until we have a unique quote number
            while True:
                quote_number = f"QTE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
                # Check if this quote number already exists
                existing_quote = Quote.query.filter_by(quote_number=quote_number).first()
                if not existing_quote:
                    app.logger.info(f"Generated new quote number: {quote_number}")
                    break
        
        # Get customer_id - check both standard field and hidden field
        customer_id = request.form.get('customer_id')
        if not customer_id:
            # Try the hidden field that might be added by JavaScript
            customer_id = request.form.get('customer_id_hidden')
            
        # Log for debugging
        app.logger.debug(f"Creating quote with customer_id: {customer_id}")
        app.logger.debug(f"Form data: {request.form}")
        
        # If customer_id is still None, default to the first customer (temporary fix)
        if not customer_id:
            first_customer = Customer.query.first()
            if first_customer:
                customer_id = first_customer.id
                app.logger.warning(f"No customer_id provided, defaulting to first customer: {customer_id}")
            else:
                flash("Error: No customer selected and no default customer available.", "danger")
                return redirect(url_for('quotes_index'))
                
        title = request.form.get('title')
        description = request.form.get('description')
        valid_until_str = request.form.get('valid_until')
        
        # Parse valid until date if provided
        valid_until = None
        if valid_until_str:
            valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')
            
        # Get the current user ID from session
        user_id = current_user.id
        app.logger.info(f"Using current user ID: {user_id} for new quote")
        
        quote = Quote(
            quote_number=quote_number,
            customer_id=customer_id,
            user_id=user_id,  # Using the current logged-in user
            title=title,
            description=description,
            valid_until=valid_until,
            status='draft'
        )
        
        try:
            db.session.add(quote)
            db.session.commit()
            app.logger.info(f"Quote created successfully with ID: {quote.id}")
            
            # Verify quote was correctly saved to database
            saved_quote = Quote.query.get(quote.id)
            if saved_quote:
                app.logger.info(f"Verified quote saved: {saved_quote.id} - {saved_quote.quote_number}")
            else:
                app.logger.error(f"Failed to verify quote with ID: {quote.id}")
                
            flash(f'Quote {quote.quote_number} created successfully. Add items to it.', 'success')
            return redirect(url_for('quotes_edit', id=quote.id))
        except Exception as e:
            app.logger.error(f"Error creating quote: {str(e)}")
            db.session.rollback()
            flash(f"Error creating quote: {str(e)}", "danger")
            return redirect(url_for('quotes_index'))
    
    # Generate a unique quote number for the form
    while True:
        quote_number = f"QTE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        # Check if this quote number already exists
        existing_quote = Quote.query.filter_by(quote_number=quote_number).first()
        if not existing_quote:
            break

    return render_template('quotes/create.html', 
                          form=form,
                          item_form=item_form,
                          customers=customers, 
                          papers=paper_options,
                          finishing_options=finishing_options,
                          quote_number=quote_number)

@app.route('/quotes/<int:id>', methods=['GET', 'POST'])
def quotes_view(id):
    from flask_wtf import FlaskForm
    from wtforms import HiddenField, SelectField
    
    # Create a form with needed fields for status updates
    class QuoteStatusForm(FlaskForm):
        status = SelectField('Status', choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ])
    
    form = QuoteStatusForm()
    quote = Quote.query.get_or_404(id)
    
    # Handle status updates
    if request.method == 'POST':
        if form.validate_on_submit():
            action = request.form.get('action')
            if action == 'update_status':
                new_status = request.form.get('status')
                if new_status in ['draft', 'sent', 'accepted', 'declined', 'expired']:
                    quote.status = new_status
                    db.session.commit()
                    flash(f'Quote status updated to {new_status}', 'success')
                else:
                    flash(f'Invalid status value: {new_status}', 'danger')
            else:
                flash('Unknown action', 'warning')
        else:
            flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
        return redirect(url_for('quotes_view', id=quote.id))
    
    # Handle conversion to order
    if request.args.get('convert_to_order') == '1':
        # Convert the quote to an order
        
        # Generate a new order number based on date and a sequential number
        date_prefix = datetime.now().strftime('%Y%m%d')
        
        # Find the highest order number with today's date prefix
        latest_order = Order.query.filter(Order.order_number.like(f'{date_prefix}%')).order_by(Order.order_number.desc()).first()
        
        if latest_order:
            try:
                # Extract the sequence number from the latest order
                sequence = int(latest_order.order_number[8:]) + 1
            except ValueError:
                # If we can't parse the sequence for some reason, start at 1
                sequence = 1
        else:
            # First order of the day
            sequence = 1
            
        # Format: YYYYMMDD-NNN
        order_number = f"{date_prefix}-{sequence:03d}"
        
        # Create a new order based on the quote
        new_order = Order(
            order_number=order_number,
            customer_id=quote.customer_id,
            user_id=current_user.id,
            title=quote.title,
            description=quote.description,
            status='new',
            due_date=datetime.now() + timedelta(days=7),  # Default due date: 1 week from now
            total_price=quote.total_price,
            quote_id=quote.id  # Link back to the original quote
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the new order ID without committing yet
        
        # Convert each quote item to an order item
        for quote_item in quote.items:
            order_item = OrderItem(
                order_id=new_order.id,
                name=quote_item.name,
                description=quote_item.description,
                sku=quote_item.sku,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                total_price=quote_item.total_price,
                status='pending'
            )
            
            db.session.add(order_item)
            db.session.flush()  # Get the new item ID without committing yet
            
            # Copy any materials from the quote item to the order item
            for quote_material in quote_item.materials:
                order_material = ItemMaterial(
                    order_item_id=order_item.id,
                    material_name=quote_material.material_name,
                    quantity=quote_material.quantity,
                    unit=quote_material.unit,
                    notes=quote_material.notes,
                    category=quote_material.category,
                    saved_price_id=quote_material.saved_price_id
                )
                
                db.session.add(order_material)
        
        # Update the quote status
        quote.status = 'accepted'
        
        # Create an activity log for both the quote and the order
        quote_activity = OrderActivity(
            order_id=new_order.id,
            user_id=current_user.id,
            activity_type='quote_converted',
            description=f'Quote #{quote.quote_number} converted to order #{new_order.order_number}'
        )
        db.session.add(quote_activity)
        
        db.session.commit()
        
        flash(f'Quote successfully converted to order #{new_order.order_number}', 'success')
        return redirect(url_for('orders_view', id=new_order.id))
    
    return render_template('quotes/view.html', quote=quote)

@app.route('/quotes/<int:id>/edit', methods=['GET', 'POST'])
def quotes_edit(id):
    from flask_wtf import FlaskForm
    from wtforms import HiddenField, StringField, TextAreaField, SelectField, DateField
    
    # Create a form with all needed fields
    class QuoteForm(FlaskForm):
        customer_id_hidden = HiddenField('Customer ID')
        quote_number = StringField('Quote Number')
        title = StringField('Title')
        description = TextAreaField('Description')
        status = SelectField('Status', choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ])
        valid_until = DateField('Valid Until', format='%Y-%m-%d', validators=[])
    
    # Create a form for quote items as well
    class QuoteItemAddForm(FlaskForm):
        name = StringField('Name')
        description = TextAreaField('Description')
        quantity = StringField('Quantity')
        unit_price = StringField('Unit Price')
    
    form = QuoteForm()
    item_form = QuoteItemAddForm()
    quote = Quote.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    if request.method == 'POST' and form.validate_on_submit():
        quote.customer_id = request.form.get('customer_id')
        quote.title = request.form.get('title')
        quote.description = request.form.get('description')
        quote.status = request.form.get('status')
        
        # Update quote number if provided
        custom_quote_number = request.form.get('quote_number')
        if custom_quote_number and custom_quote_number.strip():
            quote.quote_number = custom_quote_number.strip()
        
        valid_until_str = request.form.get('valid_until')
        if valid_until_str:
            quote.valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')
        
        db.session.commit()
        
        flash(f'Quote {quote.quote_number} updated successfully', 'success')
        return redirect(url_for('quotes_view', id=quote.id))
    
    return render_template('quotes/edit.html', 
                          quote=quote, 
                          form=form,
                          item_form=item_form,
                          customers=customers,
                          paper_options=paper_options,
                          finishing_options=finishing_options)

@app.route('/quotes/<int:id>/update', methods=['POST'])
@login_required
def quotes_update(id):
    """Update an existing quote's details"""
    from flask_wtf import FlaskForm
    from wtforms import HiddenField, StringField, TextAreaField, SelectField, DateField
    
    # Create a form with all needed fields
    class QuoteForm(FlaskForm):
        customer_id_hidden = HiddenField('Customer ID')
        quote_number = StringField('Quote Number')
        title = StringField('Title')
        description = TextAreaField('Description')
        status = SelectField('Status', choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ])
        valid_until = DateField('Valid Until', format='%Y-%m-%d', validators=[])
        
    form = QuoteForm()
    quote = Quote.query.get_or_404(id)
    
    if form.validate_on_submit():
        # Update quote fields
        quote.title = request.form.get('title', quote.title)
        quote.description = request.form.get('description', quote.description)
        status = request.form.get('status')
        if status:
            quote.status = status
            
        # Handle valid_until date
        valid_until = request.form.get('valid_until')
        if valid_until:
            try:
                quote.valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
            except ValueError:
                # If date is invalid, don't update it
                app.logger.warning(f"Invalid date format for valid_until: {valid_until}")
                
        # Update customer if changed
        customer_id = request.form.get('customer_id_hidden')
        if customer_id and int(customer_id) != quote.customer_id:
            quote.customer_id = int(customer_id)
            
        try:
            db.session.commit()
            flash('Quote updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating quote: {str(e)}")
            flash(f'Error updating quote: {str(e)}', 'danger')
            
    else:
        # Form validation failed
        flash('Invalid form submission. Please check your input.', 'danger')
        
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quotes/<int:id>/delete', methods=['POST'])
def quotes_delete(id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class QuoteDeleteForm(FlaskForm):
        pass
    
    form = QuoteDeleteForm()
    quote = Quote.query.get_or_404(id)
    quote_number = quote.quote_number
    
    if form.validate_on_submit():
        db.session.delete(quote)
        db.session.commit()
        
        flash(f'Quote {quote_number} deleted successfully', 'success')
    else:
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
    
    return redirect(url_for('quotes_index'))

# Quote PDF generation route
@app.route('/quotes/<int:id>/pdf')
def generate_pdf_quote(id):
    quote = Quote.query.get_or_404(id)
    
    # Generate PDF quote
    pdf_file = generate_quote_pdf(quote)
    
    return send_file(
        pdf_file,
        download_name=f"{quote.quote_number}_quote.pdf",
        as_attachment=True
    )

# API routes for quote item calculator are defined above in routes:
# - /api/paper-options
# - /api/print-pricing
# - /api/finishing-options

@app.route('/quotes/<int:quote_id>/items/add', methods=['GET', 'POST'])
@login_required
def quote_items_add(quote_id):
    """Add an item to a quote using a streamlined professional print shop interface"""
    app.logger.debug(f"Starting quote_items_add function with quote_id: {quote_id}")
    
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField
    
    # Create a form with all needed fields 
    class QuoteItemAddForm(FlaskForm):
        name = StringField('Name')
        description = TextAreaField('Description')
        quantity = StringField('Quantity')
        unit_price = StringField('Unit Price')
    
    form = QuoteItemAddForm()
    quote = Quote.query.get_or_404(quote_id)
    customers = Customer.query.order_by(Customer.name).all()
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    # Show the redesigned form interface for GET requests
    if request.method == 'GET':
        return render_template('quotes/basic_quote_form.html', 
                              quote=quote, 
                              form=form,
                              customers=customers,
                              paper_options=paper_options,
                              finishing_options=finishing_options)
    
    # Process form submission for POST requests
    if not form.validate_on_submit():
        app.logger.warning(f"Form validation failed: {form.errors}")
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
        return redirect(url_for('quotes_edit', id=quote.id))
    
    try:
        # Get basic item information
        name = request.form.get('name')
        description = request.form.get('description', '')
        quantity = int(request.form.get('quantity', 1))
        unit_price = float(request.form.get('unit_price', 0.0))
        
        # Get paper options
        paper_size = request.form.get('paper_size', '')
        paper_type = request.form.get('paper_type', '')
        paper_weight = request.form.get('paper_weight', '')
        paper_color = request.form.get('paper_color', '')
        
        # Get print options
        print_type = request.form.get('print_type', 'B/W')
        sides = request.form.get('sides', 'Single')
        n_up = int(request.form.get('n_up', 1))
        
        # Get finishing options
        finishing_option_list = request.form.getlist('finishing_options')
        
        # Log form data for debugging
        app.logger.debug(f"Creating quote with customer_id: {quote.customer_id}")
        app.logger.debug(f"Form data: {request.form}")
        
        # Create a detailed description based on selected options
        detailed_description = []
        
        if paper_size:
            detailed_description.append(f"Size: {paper_size}")
        
        if paper_type and paper_weight:
            detailed_description.append(f"Paper: {paper_weight} {paper_type}")
        
        if paper_color and paper_color.lower() != 'white':
            detailed_description.append(f"Color: {paper_color}")
        
        if print_type:
            detailed_description.append(f"Print: {print_type}")
        
        if sides:
            detailed_description.append(f"{sides}-sided")
        
        if n_up > 1:
            detailed_description.append(f"{n_up}-up")
        
        if finishing_option_list:
            detailed_description.append(f"Finishing: {', '.join(finishing_option_list)}")
        
        # Combine original description with detailed specs
        if description:
            full_description = f"{description}\n\n{'; '.join(detailed_description)}"
        else:
            full_description = '; '.join(detailed_description)
        
        # Create the quote item
        quote_item = QuoteItem(
            quote_id=quote_id,
            name=name,
            description=full_description,
            quantity=quantity,
            unit_price=unit_price,
            n_up=n_up
        )
        
        # Calculate total price based on unit price and add finishing costs
        finishing_cost = 0
        
        if finishing_option_list:
            for option_name in finishing_option_list:
                option = FinishingOption.query.filter_by(name=option_name).first()
                if option:
                    option_cost = option.base_price
                    
                    # Add per-piece price multiplied by quantity
                    if option.per_piece_price > 0:
                        option_cost += option.per_piece_price * quantity
                    
                    # Apply minimum price if needed
                    if option.min_price > 0 and option_cost < option.min_price:
                        option_cost = option.min_price
                    
                    # Add to total finishing cost
                    finishing_cost += option_cost
        
        # Update total price with finishing costs
        quote_item.total_price = quantity * unit_price + finishing_cost
        
        # Apply customer discount if applicable
        customer = Customer.query.get(quote.customer_id)
        if customer and customer.discount_percentage > 0:
            discount_multiplier = customer.get_discount_multiplier()
            quote_item.total_price *= discount_multiplier
            app.logger.debug(f"Applied discount: {customer.discount_percentage}%, final price: {quote_item.total_price}")
        
        # Add the quote item to the database
        db.session.add(quote_item)
        db.session.flush()  # Get the ID without committing yet
        
        # Attempt to find a matching paper option to associate with this quote item
        if paper_size and paper_type:
            paper_option = None
            
            # First try exact match on all criteria
            if paper_weight and paper_color:
                paper_option = PaperOption.query.filter(
                    PaperOption.size == paper_size,
                    PaperOption.category == paper_type,
                    PaperOption.weight == paper_weight,
                    PaperOption.color == paper_color
                ).first()
            
            # If not found, try without color
            if not paper_option and paper_weight:
                paper_option = PaperOption.query.filter(
                    PaperOption.size == paper_size,
                    PaperOption.category == paper_type,
                    PaperOption.weight == paper_weight
                ).first()
            
            # If still not found, try just size and type
            if not paper_option:
                paper_option = PaperOption.query.filter(
                    PaperOption.size == paper_size,
                    PaperOption.category == paper_type
                ).first()
            
            # If we found a paper option, associate it with the quote item
            if paper_option:
                # Create the material association
                quote_item_material = QuoteItemMaterial(
                    quote_item_id=quote_item.id,
                    material_name=paper_option.name,
                    category='paper',
                    quantity=quantity,
                    unit='sheets',
                    saved_price_id=paper_option.id
                )
                db.session.add(quote_item_material)
                app.logger.debug(f"Added paper material association: {paper_option.name}")
        
        # Update the quote's total price
        quote.update_total()
        db.session.commit()
        
        app.logger.info(f"Successfully added item to quote {quote.quote_number}")
        flash(f'Quote item "{name}" added successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding quote item: {str(e)}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error adding quote item: {str(e)}', 'danger')
    
    return redirect(url_for('quotes_edit', id=quote_id))

@app.route('/quote-items/<int:item_id>/materials/add', methods=['POST'])
@login_required
def quote_item_materials_add(item_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class QuoteMaterialAddForm(FlaskForm):
        pass
    
    form = QuoteMaterialAddForm()
    item = QuoteItem.query.get_or_404(item_id)
    
    if form.validate_on_submit():
        # Check if we're adding from a saved material or manually
        saved_material_id = request.form.get('saved_material_id')
        
        if saved_material_id and saved_material_id != 'custom':
            # Adding from saved material
            saved_price = SavedPrice.query.get_or_404(int(saved_material_id))
            material_name = saved_price.name
            category = saved_price.category
            unit = saved_price.unit
            quantity = float(request.form.get('quantity', 0.0))
            notes = request.form.get('notes')
            saved_price_id = saved_price.id
        else:
            # Manual entry
            material_name = request.form.get('material_name')
            quantity = float(request.form.get('quantity', 0.0))
            unit = request.form.get('unit')
            notes = request.form.get('notes')
            
            # Try to find a saved price for this material
            category = request.form.get('category', 'other')
            saved_price = SavedPrice.query.filter_by(name=material_name, category=category).first()
            saved_price_id = saved_price.id if saved_price else None
        
        material = QuoteItemMaterial(
            quote_item_id=item.id,
            material_name=material_name,
            quantity=quantity,
            unit=unit,
            notes=notes,
            category=category,
            saved_price_id=saved_price_id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash(f'Material added to quote item successfully', 'success')
        return redirect(url_for('quotes_edit', id=item.quote.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('quotes_edit', id=item.quote.id))

@app.route('/quote-item-materials/<int:material_id>/edit', methods=['POST'])
@login_required
def quote_item_materials_edit(material_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class QuoteMaterialEditForm(FlaskForm):
        pass
    
    form = QuoteMaterialEditForm()
    material = QuoteItemMaterial.query.get_or_404(material_id)
    item = QuoteItem.query.get(material.quote_item_id)
    
    if form.validate_on_submit():
        # Update material properties
        material.material_name = request.form.get('material_name', material.material_name)
        material.quantity = float(request.form.get('quantity', material.quantity))
        material.unit = request.form.get('unit', material.unit)
        material.notes = request.form.get('notes')
        material.category = request.form.get('category', material.category)
        
        # Check if we're changing to a saved price
        saved_material_id = request.form.get('saved_material_id')
        if saved_material_id and saved_material_id != 'custom':
            saved_price = SavedPrice.query.get_or_404(int(saved_material_id))
            material.material_name = saved_price.name
            material.category = saved_price.category
            material.unit = saved_price.unit
            material.saved_price_id = saved_price.id
        elif saved_material_id == 'custom':
            # Manually entered, remove any saved_price link
            material.saved_price_id = None
        
        db.session.commit()
        
        flash(f'Material updated successfully', 'success')
        return redirect(url_for('quotes_edit', id=item.quote.id))
    else:
        flash('Invalid form submission. Please check your input.', 'danger')
        return redirect(url_for('quotes_edit', id=item.quote.id))

@app.route('/quote-items/<int:item_id>/update', methods=['POST'])
@login_required
def quote_items_update(item_id):
    """Update an existing quote item's details"""
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField
    
    # Create a form with all needed fields
    class QuoteItemForm(FlaskForm):
        name = StringField('Name')
        description = TextAreaField('Description')
        quantity = IntegerField('Quantity')
        unit_price = FloatField('Unit Price')
        total_price = FloatField('Total Price')
        
    form = QuoteItemForm()
    item = QuoteItem.query.get_or_404(item_id)
    quote = Quote.query.get_or_404(item.quote_id)
    
    if form.validate_on_submit():
        # Update quote item fields
        item.name = request.form.get('name', item.name)
        item.description = request.form.get('description', item.description)
        item.sku = request.form.get('sku', item.sku)
        
        # Get print specifications
        item.size = request.form.get('size', item.size)
        item.custom_width = request.form.get('custom_width', item.custom_width)
        item.custom_height = request.form.get('custom_height', item.custom_height)
        item.finish_size = request.form.get('finish_size', item.finish_size)
        item.color_type = request.form.get('color_type', item.color_type)
        item.sides = request.form.get('sides', item.sides)
        
        # Get n-up value
        n_up = request.form.get('n_up', '1')
        item.n_up = int(n_up) if n_up and n_up.strip() and n_up.strip().isdigit() else 1
        
        item.paper_type = request.form.get('paper_type', item.paper_type)
        item.paper_weight = request.form.get('paper_weight', item.paper_weight)
        
        # Get finishing options
        finishing_option_list = request.form.getlist('finishing_options')
        if finishing_option_list:
            item.finishing_options = ','.join(finishing_option_list)
        
        # Get quantity and price
        quantity = request.form.get('quantity')
        if quantity:
            item.quantity = int(quantity)
            
        unit_price = request.form.get('unit_price')
        if unit_price:
            item.unit_price = float(unit_price)
        
        # Recalculate total price
        item.total_price = item.quantity * item.unit_price
        
        # Calculate finishing option costs (similar to item add)
        finishing_cost = 0
        if finishing_option_list:
            for option_name in finishing_option_list:
                # Look up finishing option details from database
                option = FinishingOption.query.filter_by(name=option_name).first()
                if option:
                    # Calculate the cost for this option
                    option_cost = option.base_price
                    
                    # Add per-piece price multiplied by quantity
                    if option.price_per_piece > 0:
                        option_cost += option.price_per_piece * item.quantity
                    
                    # Apply minimum price if needed
                    if option.minimum_price > 0 and option_cost < option.minimum_price:
                        option_cost = option.minimum_price
                    
                    # Add to total finishing cost
                    finishing_cost += option_cost
        
        # Add finishing costs to total price
        item.total_price += finishing_cost
        
        # Apply customer discount if applicable
        customer = Customer.query.get(quote.customer_id)
        if customer and customer.discount_percentage > 0:
            discount_multiplier = customer.get_discount_multiplier()
            item.total_price = item.total_price * discount_multiplier
        
        # Update booklet fields if applicable
        product_type = request.form.get('product_type')
        if product_type:
            item.product_type = product_type
            
        if product_type == 'booklet':
            page_count = request.form.get('page_count')
            if page_count:
                item.page_count = int(page_count)
                
            item.cover_paper_type = request.form.get('cover_paper_type', item.cover_paper_type)
            item.binding_type = request.form.get('binding_type', item.binding_type)
            item.cover_printing = request.form.get('cover_printing', item.cover_printing)
            item.self_cover = request.form.get('self_cover') == 'on'
        
        try:
            # Update the quote's total price
            quote_items = QuoteItem.query.filter_by(quote_id=quote.id).all()
            quote.total_price = sum(i.total_price for i in quote_items if i.id != item.id) + item.total_price
            
            db.session.commit()
            flash('Quote item updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating quote item: {str(e)}")
            flash(f'Error updating quote item: {str(e)}', 'danger')
            
    else:
        # Form validation failed
        flash('Invalid form submission. Please check your input.', 'danger')
        
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quote-item-materials/<int:material_id>/delete', methods=['POST'])
@login_required
def quote_item_materials_delete(material_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class QuoteMaterialDeleteForm(FlaskForm):
        pass
    
    form = QuoteMaterialDeleteForm()
    material = QuoteItemMaterial.query.get_or_404(material_id)
    item = QuoteItem.query.get(material.quote_item_id)
    
    if form.validate_on_submit():
        quote_id = item.quote.id
        material_name = material.material_name
        
        db.session.delete(material)
        db.session.commit()
        
        flash(f'Material "{material_name}" deleted successfully', 'success')
        return redirect(url_for('quotes_edit', id=quote_id))
    else:
        flash('Invalid form submission.', 'danger')
        return redirect(url_for('quotes_edit', id=item.quote.id))

@app.route('/quotes/items/<int:item_id>/edit', methods=['POST'])
def quote_items_edit(item_id):
    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField
    
    # Create a form with all needed fields
    class QuoteItemEditForm(FlaskForm):
        name = StringField('Name')
        description = TextAreaField('Description')
        quantity = IntegerField('Quantity')
        unit_price = FloatField('Unit Price')
        total_price = FloatField('Total Price')
    
    form = QuoteItemEditForm()
    item = QuoteItem.query.get_or_404(item_id)
    quote = item.quote
    
    if not form.validate_on_submit():
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
        return redirect(url_for('quotes_edit', id=quote.id))
    
    item.name = request.form.get('name')
    item.description = request.form.get('description')
    item.sku = request.form.get('sku')
    
    # Update product type
    item.product_type = request.form.get('product_type', 'print_job')
    
    # Update booklet fields if this is a booklet
    if item.product_type == 'booklet':
        page_count = request.form.get('page_count')
        if page_count:
            item.page_count = int(page_count)
        item.cover_paper_type = request.form.get('cover_paper_type')
        item.binding_type = request.form.get('binding_type')
        item.cover_printing = request.form.get('cover_printing')
        item.self_cover = request.form.get('self_cover') == 'on'
    
    # Update print specifications
    item.size = request.form.get('size')
    item.custom_width = request.form.get('custom_width')
    item.custom_height = request.form.get('custom_height')
    item.finish_size = request.form.get('finish_size')
    item.color_type = request.form.get('color_type')
    item.sides = request.form.get('sides')
    
    # Get n_up and convert to integer
    n_up = request.form.get('n_up', '1') 
    item.n_up = int(n_up) if n_up and n_up.strip() and n_up.strip().isdigit() else 1
    
    item.paper_type = request.form.get('paper_type')
    item.paper_weight = request.form.get('paper_weight')
    
    # Update finishing options and calculate their costs
    finishing_option_list = request.form.getlist('finishing_options')
    item.finishing_options = ','.join(finishing_option_list)
    
    item.quantity = int(request.form.get('quantity', 1))
    item.unit_price = float(request.form.get('unit_price', 0.0))
    
    # Calculate base price without finishing options
    base_price = item.quantity * item.unit_price
    
    # Calculate finishing option costs
    finishing_cost = 0
    if finishing_option_list:
        for option_name in finishing_option_list:
            # Look up finishing option details from database
            option = FinishingOption.query.filter_by(name=option_name).first()
            if option:
                # Calculate the cost for this option
                option_cost = option.base_price
                
                # Add per-piece price multiplied by quantity
                if option.price_per_piece > 0:
                    option_cost += option.price_per_piece * item.quantity
                
                # For future: add per-sqft calculations if needed
                
                # Apply minimum price if needed
                if option.minimum_price > 0 and option_cost < option.minimum_price:
                    option_cost = option.minimum_price
                
                # Add to total finishing cost
                finishing_cost += option_cost
    
    # Calculate total price including finishing costs
    total_price = base_price + finishing_cost
    
    # Apply customer discount if applicable
    customer = Customer.query.get(quote.customer_id)
    if customer and customer.discount_percentage > 0:
        discount_multiplier = customer.get_discount_multiplier()
        discounted_total = total_price * discount_multiplier
        
        # Log the discount for debugging
        print(f"DEBUG: Applied customer discount on quote item edit: {customer.discount_percentage}% - Original: {total_price} -> Discounted: {discounted_total}")
        
        # Update total price with discount
        total_price = discounted_total
    
    item.total_price = total_price
    
    # Update quote total
    quote.total_price = sum(i.total_price for i in quote.items)
    
    db.session.commit()
    
    flash(f'Item updated successfully', 'success')
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quotes/items/<int:item_id>/delete', methods=['POST'])
def quote_items_delete(item_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class QuoteItemDeleteForm(FlaskForm):
        pass
    
    form = QuoteItemDeleteForm()
    item = QuoteItem.query.get_or_404(item_id)
    quote = item.quote
    
    if form.validate_on_submit():
        item_name = item.name
        
        db.session.delete(item)
        
        # Update quote total
        quote.total_price = sum(i.total_price for i in quote.items if i.id != item_id)
        
        db.session.commit()
        
        flash(f'Item removed from quote successfully', 'success')
    else:
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
    
    return redirect(url_for('quotes_edit', id=quote.id))

# This section was removed to prevent duplicate route definitions 
# as routes /api/paper-options and /api/print-pricing are already defined earlier in the file

# API endpoint for finishing options is defined earlier in the file at line 1955.

# Admin routes for managing paper and finishing options
@app.route('/paper-options')
@login_required
def paper_options_index():
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    return render_template('paper_options/index.html', paper_options=paper_options)

# Print pricing routes
@app.route('/print-pricing')
@login_required
def print_pricing_index():
    pricing_options = PrintPricing.query.order_by(PrintPricing.paper_size, PrintPricing.color_type).all()
    return render_template('print_pricing/index.html', pricing_options=pricing_options)

@app.route('/print-pricing/create', methods=['GET', 'POST'])
@login_required
def print_pricing_create():
    if request.method == 'POST':
        name = request.form.get('name')
        paper_size = request.form.get('paper_size')
        color_type = request.form.get('color_type')
        price_per_side = float(request.form.get('price_per_side', 0.0))
        cost_per_side = float(request.form.get('cost_per_side', 0.0))
        price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        cost_per_sqft = float(request.form.get('cost_per_sqft', 0.0))
        pricing_method = request.form.get('pricing_method', 'side')
        notes = request.form.get('notes')
        
        pricing = PrintPricing(
            name=name,
            paper_size=paper_size,
            color_type=color_type,
            price_per_side=price_per_side,
            cost_per_side=cost_per_side,
            price_per_sqft=price_per_sqft,
            cost_per_sqft=cost_per_sqft,
            pricing_method=pricing_method,
            notes=notes
        )
        
        db.session.add(pricing)
        db.session.commit()
        
        flash(f'Print pricing "{name}" created successfully', 'success')
        return redirect(url_for('print_pricing_index'))
    
    return render_template('print_pricing/create.html')

@app.route('/print-pricing/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def print_pricing_edit(id):
    pricing = PrintPricing.query.get_or_404(id)
    
    if request.method == 'POST':
        pricing.name = request.form.get('name')
        pricing.paper_size = request.form.get('paper_size')
        pricing.color_type = request.form.get('color_type')
        pricing.price_per_side = float(request.form.get('price_per_side', 0.0))
        pricing.cost_per_side = float(request.form.get('cost_per_side', 0.0))
        pricing.price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        pricing.cost_per_sqft = float(request.form.get('cost_per_sqft', 0.0))
        pricing.pricing_method = request.form.get('pricing_method', 'side')
        pricing.notes = request.form.get('notes')
        
        db.session.commit()
        
        flash(f'Print pricing "{pricing.name}" updated successfully', 'success')
        return redirect(url_for('print_pricing_index'))
    
    return render_template('print_pricing/edit.html', pricing=pricing)

@app.route('/print-pricing/<int:id>/delete', methods=['POST'])
@login_required
def print_pricing_delete(id):
    pricing = PrintPricing.query.get_or_404(id)
    name = pricing.name
    
    db.session.delete(pricing)
    db.session.commit()
    
    flash(f'Print pricing "{name}" deleted successfully', 'success')
    return redirect(url_for('print_pricing_index'))

@app.route('/paper-options/create', methods=['GET', 'POST'])
@login_required
def paper_options_create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        weight = request.form.get('weight')
        size = request.form.get('size')
        color = request.form.get('color')
        price_per_sheet = float(request.form.get('price_per_sheet', 0.0))
        cost_per_sheet = float(request.form.get('cost_per_sheet', 0.0))
        price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        cost_per_sqft = float(request.form.get('cost_per_sqft', 0.0))
        width = request.form.get('width')
        height = request.form.get('height')
        pricing_method = request.form.get('pricing_method', 'sheet')
        
        # Convert numerical values to float if provided
        width = float(width) if width else None
        height = float(height) if height else None
        roll_length = request.form.get('roll_length')
        roll_length = float(roll_length) if roll_length else None
        is_roll = 'is_roll' in request.form
        
        paper_option = PaperOption(
            name=name,
            description=description,
            category=category,
            weight=weight,
            size=size,
            color=color,
            price_per_sheet=price_per_sheet,
            cost_per_sheet=cost_per_sheet,
            price_per_sqft=price_per_sqft,
            cost_per_sqft=cost_per_sqft,
            width=width,
            height=height,
            roll_length=roll_length,
            is_roll=is_roll,
            pricing_method=pricing_method
        )
        
        db.session.add(paper_option)
        db.session.commit()
        
        flash(f'Paper option "{name}" created successfully', 'success')
        return redirect(url_for('paper_options_index'))
    
    return render_template('paper_options/create.html')

@app.route('/paper-options/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def paper_options_edit(id):
    paper_option = PaperOption.query.get_or_404(id)
    
    if request.method == 'POST':
        paper_option.name = request.form.get('name')
        paper_option.description = request.form.get('description')
        paper_option.category = request.form.get('category')
        paper_option.weight = request.form.get('weight')
        paper_option.size = request.form.get('size')
        paper_option.color = request.form.get('color')
        paper_option.price_per_sheet = float(request.form.get('price_per_sheet', 0.0))
        paper_option.cost_per_sheet = float(request.form.get('cost_per_sheet', 0.0))
        paper_option.price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        paper_option.cost_per_sqft = float(request.form.get('cost_per_sqft', 0.0))
        paper_option.pricing_method = request.form.get('pricing_method', 'sheet')
        
        # Convert numerical values to float if provided
        width = request.form.get('width')
        height = request.form.get('height')
        roll_length = request.form.get('roll_length')
        paper_option.width = float(width) if width else None
        paper_option.height = float(height) if height else None
        paper_option.roll_length = float(roll_length) if roll_length else None
        paper_option.is_roll = 'is_roll' in request.form
        
        db.session.commit()
        
        flash(f'Paper option "{paper_option.name}" updated successfully', 'success')
        return redirect(url_for('paper_options_index'))
    
    return render_template('paper_options/edit.html', paper_option=paper_option)

@app.route('/paper-options/<int:id>/delete', methods=['POST'])
@login_required
def paper_options_delete(id):
    paper_option = PaperOption.query.get_or_404(id)
    
    try:
        db.session.delete(paper_option)
        db.session.commit()
        flash('Paper option deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting paper option: {str(e)}', 'danger')
    
    return redirect(url_for('paper_options_index'))

@app.route('/finishing-options')
@login_required
def finishing_options_index():
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    return render_template('finishing_options/index.html', finishing_options=finishing_options)

@app.route('/finishing-options/create', methods=['GET', 'POST'])
@login_required
def finishing_options_create():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        base_price = float(request.form.get('base_price', 0.0))
        price_per_piece = float(request.form.get('price_per_piece', 0.0))
        price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        minimum_price = float(request.form.get('minimum_price', 0.0))
        
        finishing_option = FinishingOption(
            name=name,
            description=description,
            category=category,
            base_price=base_price,
            price_per_piece=price_per_piece,
            price_per_sqft=price_per_sqft,
            minimum_price=minimum_price
        )
        
        db.session.add(finishing_option)
        db.session.commit()
        
        flash(f'Finishing option "{name}" created successfully', 'success')
        return redirect(url_for('finishing_options_index'))
    
    return render_template('finishing_options/create.html')

@app.route('/finishing-options/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def finishing_options_edit(id):
    finishing_option = FinishingOption.query.get_or_404(id)
    
    if request.method == 'POST':
        finishing_option.name = request.form.get('name')
        finishing_option.description = request.form.get('description')
        finishing_option.category = request.form.get('category')
        finishing_option.base_price = float(request.form.get('base_price', 0.0))
        finishing_option.price_per_piece = float(request.form.get('price_per_piece', 0.0))
        finishing_option.price_per_sqft = float(request.form.get('price_per_sqft', 0.0))
        finishing_option.minimum_price = float(request.form.get('minimum_price', 0.0))
        
        db.session.commit()
        
        flash(f'Finishing option "{finishing_option.name}" updated successfully', 'success')
        return redirect(url_for('finishing_options_index'))
    
    return render_template('finishing_options/edit.html', finishing_option=finishing_option)

# Proof Approval Routes
@app.route('/files/<int:file_id>/send-proof', methods=['POST'])
def send_proof_email(file_id):
    """Send a proof to a customer via email for approval"""
    order_file = OrderFile.query.get_or_404(file_id)
    order = order_file.order
    customer = order.customer
    
    # Check if file type is appropriate for proofing
    if order_file.file_type not in ['proof', 'artwork']:
        flash('Only proof or artwork files can be sent for approval', 'danger')
        return redirect(url_for('files_preview', file_id=file_id))
    
    # Get the base URL from request
    base_url = request.url_root.rstrip('/')
    
    # Send the proof approval email
    success = send_proof_approval_email(order_file, customer, order, base_url)
    
    if success:
        # Save changes to the database
        db.session.commit()
        
        # Create activity log
        activity = OrderActivity(
            order_id=order.id,
            user_id=order.user_id,  # Use the order creator's user ID
            activity_type='proof_sent',
            description=f'Proof "{order_file.original_filename}" sent to customer {customer.name} for approval'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Proof sent to customer for approval', 'success')
    else:
        flash('Failed to send proof email. Please check email settings.', 'danger')
    
    return redirect(url_for('files_preview', file_id=file_id))

@app.route('/proof/view/<token>')
def proof_view(token):
    """View a proof using a token (no login required)"""
    # Find the file by token
    file = OrderFile.query.filter_by(approval_token=token).first_or_404()
    order = file.order
    customer = order.customer
    
    # Get the preview URL
    preview_url = nextcloud.get_preview_url(file.file_path)
    
    # Generate URLs for actions
    approve_url = url_for('proof_approve', token=token)
    reject_url = url_for('proof_reject', token=token)
    download_url = url_for('proof_download', token=token)
    
    return render_template('proof/view.html', 
                           file=file, 
                           order=order, 
                           customer=customer,
                           preview_url=preview_url,
                           approve_url=approve_url,
                           reject_url=reject_url,
                           download_url=download_url)

@app.route('/proof/download/<token>')
def proof_download(token):
    """Download a proof using a token (no login required)"""
    # Find the file by token
    file = OrderFile.query.filter_by(approval_token=token).first_or_404()
    
    # Download file from Nextcloud
    temp_file_path = nextcloud.download_file(file.file_path)
    
    if temp_file_path:
        return send_file(
            temp_file_path,
            download_name=file.original_filename,
            as_attachment=True
        )
    else:
        flash('Failed to download file', 'danger')
        return redirect(url_for('proof_view', token=token))

@app.route('/proof/approve/<token>')
def proof_approve(token):
    """Approve a proof using a token (no login required)"""
    # Find the file by token
    file = OrderFile.query.filter_by(approval_token=token).first_or_404()
    order = file.order
    customer = order.customer
    
    # Update approval status
    file.approval_status = 'approved'
    file.approval_date = datetime.utcnow()
    db.session.commit()
    
    # Create activity log
    activity = OrderActivity(
        order_id=order.id,
        user_id=None,  # No user for customer action
        activity_type='proof_approved',
        description=f'Proof "{file.original_filename}" approved by customer {customer.name}'
    )
    db.session.add(activity)
    db.session.commit()
    
    view_url = url_for('proof_view', token=token)
    
    return render_template('proof/confirmation.html',
                           action_type='approved',
                           file=file,
                           order=order,
                           customer=customer,
                           view_url=view_url)

@app.route('/proof/reject/<token>')
def proof_reject(token):
    """Show the rejection form when a customer wants to request changes"""
    # Find the file by token
    file = OrderFile.query.filter_by(approval_token=token).first_or_404()
    order = file.order
    customer = order.customer
    
    # Get the preview URL
    preview_url = nextcloud.get_preview_url(file.file_path)
    
    # Generate URLs
    view_url = url_for('proof_view', token=token)
    reject_submit_url = url_for('proof_reject_submit', token=token)
    download_url = url_for('proof_download', token=token)
    
    return render_template('proof/reject_form.html',
                           file=file,
                           order=order,
                           customer=customer,
                           preview_url=preview_url,
                           view_url=view_url,
                           reject_submit_url=reject_submit_url,
                           token=token,
                           download_url=download_url)

@app.route('/proof/reject-submit/<token>', methods=['POST'])
def proof_reject_submit(token):
    """Process the rejection form submission"""
    # Find the file by token
    file = OrderFile.query.filter_by(approval_token=token).first_or_404()
    order = file.order
    customer = order.customer
    
    # Get the comment from the form
    comment = request.form.get('comment', '')
    
    # Update approval status
    file.approval_status = 'rejected'
    file.approval_date = datetime.utcnow()
    file.approval_comment = comment
    db.session.commit()
    
    # Create activity log
    activity = OrderActivity(
        order_id=order.id,
        user_id=None,  # No user for customer action
        activity_type='proof_rejected',
        description=f'Proof "{file.original_filename}" rejected by customer {customer.name} with comment: {comment}'
    )
    db.session.add(activity)
    db.session.commit()
    
    view_url = url_for('proof_view', token=token)
    
    return render_template('proof/confirmation.html',
                           action_type='rejected',
                           file=file,
                           order=order,
                           customer=customer,
                           view_url=view_url,
                           comment=comment)

# Export download route
@app.route('/download_export/<filename>')
def download_export(filename):
    """Download an export file"""
    # Security check - only allow zip files with printshop_export prefix
    if not (filename.startswith('printshop_export_') and filename.endswith('.zip')):
        flash('Invalid export file', 'error')
        return redirect(url_for('dashboard'))
        
    # Check if file exists
    if not os.path.exists(filename):
        flash('Export file not found', 'error')
        return redirect(url_for('dashboard'))
        
    # Return file as attachment
    return send_file(filename,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/zip')

# ============================================================================
# Reports Routes
# ============================================================================

@app.route('/reports')
@login_required
def reports_index():
    """Reports dashboard page"""
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('reports/index.html', customers=customers)

@app.route('/reports/profitability')
@login_required
def reports_profitability():
    """Profitability report showing cost vs. profit analysis"""
    # Get all orders
    orders = Order.query.all()
    
    # Calculate costs for each order
    order_costs = {}
    total_revenue = 0
    total_cost = 0
    
    for order in orders:
        # Calculate material costs for this order
        order_cost = 0
        for item in order.items:
            for material in item.materials:
                # If this material has a saved price with a cost price, use that
                if material.saved_price and material.saved_price.cost_price:
                    material_cost = material.saved_price.cost_price * material.quantity
                    order_cost += material_cost
        
        order_costs[order.id] = order_cost
        total_revenue += order.total_price
        total_cost += order_cost
    
    # Calculate profit and margin
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Calculate profitability by customer
    customer_profitability = {}
    
    for order in orders:
        customer_id = order.customer_id
        customer_name = order.customer.name
        
        if customer_id not in customer_profitability:
            customer_profitability[customer_id] = {
                'name': customer_name,
                'order_count': 0,
                'revenue': 0,
                'cost': 0,
                'profit': 0,
                'margin': 0
            }
        
        customer_profitability[customer_id]['order_count'] += 1
        customer_profitability[customer_id]['revenue'] += order.total_price
        customer_profitability[customer_id]['cost'] += order_costs[order.id]
    
    # Calculate profit and margin for each customer
    for customer_id, data in customer_profitability.items():
        data['profit'] = data['revenue'] - data['cost']
        data['margin'] = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
    
    return render_template('reports/profitability.html',
                           orders=orders,
                           order_costs=order_costs,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           profit_margin=profit_margin,
                           customer_profitability=customer_profitability)

@app.route('/reports/customer')
@login_required
def reports_customer():
    """Report for a specific customer"""
    customer_id = request.args.get('customer_id')
    
    if not customer_id:
        flash('Please select a customer', 'warning')
        return redirect(url_for('reports_index'))
    
    customer = Customer.query.get_or_404(customer_id)
    
    # Get all orders for this customer
    orders = Order.query.filter_by(customer_id=customer_id).all()
    
    # Get all quotes for this customer
    quotes = Quote.query.filter_by(customer_id=customer_id).all()
    
    # Calculate order costs
    order_costs = {}
    total_revenue = 0
    total_cost = 0
    
    for order in orders:
        # Calculate material costs for this order
        order_cost = 0
        for item in order.items:
            for material in item.materials:
                # If this material has a saved price with a cost price, use that
                if material.saved_price and material.saved_price.cost_price:
                    material_cost = material.saved_price.cost_price * material.quantity
                    order_cost += material_cost
        
        order_costs[order.id] = order_cost
        total_revenue += order.total_price
        total_cost += order_cost
    
    # Calculate profit and margin
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Prepare yearly data for charts
    yearly_data = {}
    for order in orders:
        year = order.created_at.strftime('%Y')
        if year not in yearly_data:
            yearly_data[year] = {
                'order_count': 0,
                'revenue': 0,
                'cost': 0,
                'profit': 0
            }
        
        yearly_data[year]['order_count'] += 1
        yearly_data[year]['revenue'] += order.total_price
        yearly_data[year]['cost'] += order_costs[order.id]
        yearly_data[year]['profit'] += (order.total_price - order_costs[order.id])
    
    return render_template('reports/customer.html',
                           customer=customer,
                           orders=orders,
                           quotes=quotes,
                           order_costs=order_costs,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           profit_margin=profit_margin,
                           order_count=len(orders),
                           yearly_data=yearly_data)

@app.route('/reports/customers')
@login_required
def reports_customers():
    """Report for all customers"""
    customers = Customer.query.order_by(Customer.name).all()
    
    # Prepare customer data
    customer_data = {}
    total_revenue = 0
    total_cost = 0
    
    for customer in customers:
        # Get all orders for this customer
        orders = Order.query.filter_by(customer_id=customer.id).all()
        
        # Calculate costs and revenue
        customer_revenue = 0
        customer_cost = 0
        
        for order in orders:
            customer_revenue += order.total_price
            
            # Calculate material costs for this order
            order_cost = 0
            for item in order.items:
                for material in item.materials:
                    # If this material has a saved price with a cost price, use that
                    if material.saved_price and material.saved_price.cost_price:
                        material_cost = material.saved_price.cost_price * material.quantity
                        order_cost += material_cost
            
            customer_cost += order_cost
        
        # Calculate profit and margin
        customer_profit = customer_revenue - customer_cost
        customer_margin = (customer_profit / customer_revenue * 100) if customer_revenue > 0 else 0
        
        customer_data[customer.id] = {
            'name': customer.name,
            'order_count': len(orders),
            'revenue': customer_revenue,
            'cost': customer_cost,
            'profit': customer_profit,
            'margin': customer_margin
        }
        
        total_revenue += customer_revenue
        total_cost += customer_cost
    
    # Calculate totals
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    return render_template('reports/customers.html',
                           customers=customers,
                           customer_data=customer_data,
                           customer_count=len(customers),
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           profit_margin=profit_margin)

@app.route('/reports/time-period')
@login_required
def reports_time_period():
    """Report for a specific time period"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # If no dates provided, default to current month
    if not start_date_str or not end_date_str:
        today = datetime.today()
        start_date = datetime(today.year, today.month, 1)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = today.strftime('%Y-%m-%d')
    
    # Parse dates
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Make end_date inclusive by setting it to the end of the day
    end_date = datetime.combine(end_date.date(), datetime.max.time())
    
    # Get orders in the date range
    orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date).all()
    
    # Calculate order costs
    order_costs = {}
    total_revenue = 0
    total_cost = 0
    
    for order in orders:
        # Calculate material costs for this order
        order_cost = 0
        for item in order.items:
            for material in item.materials:
                # If this material has a saved price with a cost price, use that
                if material.saved_price and material.saved_price.cost_price:
                    material_cost = material.saved_price.cost_price * material.quantity
                    order_cost += material_cost
        
        order_costs[order.id] = order_cost
        total_revenue += order.total_price
        total_cost += order_cost
    
    # Calculate profit and margin
    total_profit = total_revenue - total_cost
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Prepare monthly data for charts
    monthly_data = {}
    for order in orders:
        month = order.created_at.strftime('%Y-%m')
        if month not in monthly_data:
            monthly_data[month] = {
                'order_count': 0,
                'revenue': 0,
                'cost': 0,
                'profit': 0
            }
        
        monthly_data[month]['order_count'] += 1
        monthly_data[month]['revenue'] += order.total_price
        monthly_data[month]['cost'] += order_costs[order.id]
        monthly_data[month]['profit'] += (order.total_price - order_costs[order.id])
    
    # Prepare customer data for this period
    customer_data = {}
    
    for order in orders:
        customer_id = order.customer_id
        if customer_id not in customer_data:
            customer_data[customer_id] = {
                'name': order.customer.name,
                'order_count': 0,
                'revenue': 0,
                'cost': 0,
                'profit': 0
            }
        
        customer_data[customer_id]['order_count'] += 1
        customer_data[customer_id]['revenue'] += order.total_price
        customer_data[customer_id]['cost'] += order_costs[order.id]
        customer_data[customer_id]['profit'] += (order.total_price - order_costs[order.id])
    
    return render_template('reports/time_period.html',
                           start_date=start_date_str,
                           end_date=end_date_str,
                           orders=orders,
                           order_costs=order_costs,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           total_profit=total_profit,
                           profit_margin=profit_margin,
                           order_count=len(orders),
                           monthly_data=monthly_data,
                           customer_data=customer_data)

@app.route('/reports/materials')
@login_required
def reports_materials():
    """Materials usage report"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # If no dates provided, default to all-time
    if start_date_str and end_date_str:
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Make end_date inclusive by setting it to the end of the day
        end_date = datetime.combine(end_date.date(), datetime.max.time())
        
        # Get orders in the date range
        orders = Order.query.filter(Order.created_at >= start_date, Order.created_at <= end_date).all()
    else:
        # Get all orders
        orders = Order.query.all()
        
        # Set default date strings for the template
        if orders:
            start_date_str = min(order.created_at for order in orders).strftime('%Y-%m-%d')
            end_date_str = max(order.created_at for order in orders).strftime('%Y-%m-%d')
        else:
            today = datetime.today()
            start_date_str = today.replace(day=1).strftime('%Y-%m-%d')
            end_date_str = today.strftime('%Y-%m-%d')
    
    # Analyze materials usage
    materials_by_name = {}
    materials_by_category = {}
    total_material_cost = 0
    
    for order in orders:
        for item in order.items:
            for material in item.materials:
                material_name = material.material_name
                material_category = material.category or 'Other'
                material_quantity = material.quantity or 0
                material_unit = material.unit or 'pcs'
                
                # Calculate material cost
                material_cost = 0
                if material.saved_price and material.saved_price.cost_price:
                    material_cost = material.saved_price.cost_price * material_quantity
                
                # Add to materials by name dictionary
                if material_name not in materials_by_name:
                    materials_by_name[material_name] = {
                        'name': material_name,
                        'category': material_category,
                        'total_quantity': 0,
                        'unit': material_unit,
                        'total_cost': 0,
                        'order_count': 0,
                        'orders': set(),
                        'id': material.id if hasattr(material, 'id') else None
                    }
                
                materials_by_name[material_name]['total_quantity'] += material_quantity
                materials_by_name[material_name]['total_cost'] += material_cost
                materials_by_name[material_name]['orders'].add(order.id)
                
                # Add to materials by category dictionary
                if material_category not in materials_by_category:
                    materials_by_category[material_category] = {
                        'quantity': 0,
                        'cost': 0,
                        'percentage': 0
                    }
                
                materials_by_category[material_category]['quantity'] += material_quantity
                materials_by_category[material_category]['cost'] += material_cost
                
                # Add to total cost
                total_material_cost += material_cost
    
    # Calculate order counts and percentages
    for material_name, data in materials_by_name.items():
        data['order_count'] = len(data['orders'])
        del data['orders']  # Remove the set to make it JSON serializable
    
    for category, data in materials_by_category.items():
        data['percentage'] = (data['cost'] / total_material_cost * 100) if total_material_cost > 0 else 0
    
    # Sort materials by cost
    top_materials = sorted(
        materials_by_name.values(),
        key=lambda x: x['total_cost'],
        reverse=True
    )[:20]
    
    # Prepare top 5 materials for trend chart
    top_materials_for_trend = sorted(
        materials_by_name.values(),
        key=lambda x: x['total_cost'],
        reverse=True
    )[:5]
    
    # Calculate monthly material usage for trending
    monthly_material_usage = {}
    
    for order in orders:
        month = order.created_at.strftime('%Y-%m')
        
        if month not in monthly_material_usage:
            monthly_material_usage[month] = {}
        
        for item in order.items:
            for material in item.materials:
                material_id = material.id if hasattr(material, 'id') else f"noname_{material.material_name}"
                material_quantity = material.quantity or 0
                
                # Calculate material cost
                material_cost = 0
                if material.saved_price and material.saved_price.cost_price:
                    material_cost = material.saved_price.cost_price * material_quantity
                
                if material_id not in monthly_material_usage[month]:
                    monthly_material_usage[month][material_id] = {
                        'quantity': 0,
                        'cost': 0
                    }
                
                monthly_material_usage[month][material_id]['quantity'] += material_quantity
                monthly_material_usage[month][material_id]['cost'] += material_cost
    
    # Get orders sorted by material cost
    orders_with_material_cost = []
    for order in orders:
        material_cost = 0
        for item in order.items:
            for material in item.materials:
                if material.saved_price and material.saved_price.cost_price:
                    material_cost += material.saved_price.cost_price * (material.quantity or 0)
        
        # Calculate percentage of total cost
        material_cost_percentage = 0
        if order.total_price > 0:
            material_cost_percentage = (material_cost / order.total_price * 100)
        
        orders_with_material_cost.append({
            'order': order,
            'material_cost': material_cost,
            'material_cost_percentage': material_cost_percentage
        })
    
    # Sort orders by material cost
    orders_by_material_cost = sorted(
        orders_with_material_cost,
        key=lambda x: x['material_cost'],
        reverse=True
    )[:15]
    
    # Convert to template-friendly format
    orders_by_material_cost = [{
        'id': o['order'].id,
        'order_number': o['order'].order_number,
        'created_at': o['order'].created_at,
        'customer': o['order'].customer,
        'title': o['order'].title,
        'material_cost': o['material_cost'],
        'material_cost_percentage': o['material_cost_percentage']
    } for o in orders_by_material_cost]
    
    return render_template('reports/materials.html',
                           start_date=start_date_str,
                           end_date=end_date_str,
                           total_material_cost=total_material_cost,
                           orders_with_materials_count=len([o for o in orders if any(item.materials for item in o.items)]),
                           unique_materials_count=len(materials_by_name),
                           materials_by_category=materials_by_category,
                           top_materials=top_materials,
                           top_materials_for_trend=top_materials_for_trend,
                           monthly_material_usage=monthly_material_usage,
                           orders_by_material_cost=orders_by_material_cost)

@app.route('/reports/accounts-receivable')
@login_required
def reports_accounts_receivable():
    """Accounts receivable report showing customer balances and outstanding orders"""
    from datetime import date, timedelta
    
    # Get all orders that aren't fully paid
    orders = Order.query.filter(
        Order.payment_status.in_(['unpaid', 'partial'])
    ).order_by(Order.due_date).all()
    
    # Calculate aging for each order
    today = date.today()
    
    # Initialize customer balances
    customer_balances = {}
    total_receivable = 0
    current_receivable = 0
    days_1_30 = 0
    days_31_60 = 0
    days_61_90 = 0
    days_over_90 = 0
    
    # Process each order
    outstanding_orders = []
    for order in orders:
        customer_id = order.customer_id
        if customer_id not in customer_balances:
            customer_balances[customer_id] = {
                'name': order.customer.name,
                'email': order.customer.email,
                'total_due': 0,
                'current': 0,
                'days_1_30': 0, 
                'days_31_60': 0,
                'days_61_90': 0,
                'days_over_90': 0
            }
        
        # Calculate balance due on this order
        balance_due = order.balance_due
        
        if balance_due <= 0:
            continue  # Skip fully paid orders
        
        # Calculate age of the order based on due date or creation date
        if order.due_date:
            invoice_date = order.due_date.date()
        else:
            invoice_date = order.created_at.date()
        
        days_outstanding = (today - invoice_date).days
        
        # Add this order to outstanding orders list
        order.days_outstanding = days_outstanding
        outstanding_orders.append(order)
        
        # Add to customer's appropriate aging bucket
        if days_outstanding <= 0:  # Not due yet
            customer_balances[customer_id]['current'] += balance_due
            current_receivable += balance_due
        elif days_outstanding <= 30:
            customer_balances[customer_id]['days_1_30'] += balance_due
            days_1_30 += balance_due
        elif days_outstanding <= 60:
            customer_balances[customer_id]['days_31_60'] += balance_due
            days_31_60 += balance_due
        elif days_outstanding <= 90:
            customer_balances[customer_id]['days_61_90'] += balance_due
            days_61_90 += balance_due
        else:
            customer_balances[customer_id]['days_over_90'] += balance_due
            days_over_90 += balance_due
        
        # Add to customer's total
        customer_balances[customer_id]['total_due'] += balance_due
        total_receivable += balance_due
    
    # Add all customers (even with zero balance) to the list
    all_customers = Customer.query.all()
    for customer in all_customers:
        if customer.id not in customer_balances:
            customer_balances[customer.id] = {
                'name': customer.name,
                'email': customer.email,
                'total_due': 0,
                'current': 0,
                'days_1_30': 0, 
                'days_31_60': 0,
                'days_61_90': 0,
                'days_over_90': 0
            }
    
    # Sort outstanding orders by days outstanding (oldest first)
    outstanding_orders.sort(key=lambda o: o.days_outstanding, reverse=True)
    
    # Calculate percentages for aging chart
    total = total_receivable or 1  # Avoid division by zero
    current_percentage = (current_receivable / total) * 100
    days_1_30_percentage = (days_1_30 / total) * 100
    days_31_60_percentage = (days_31_60 / total) * 100
    days_61_90_percentage = (days_61_90 / total) * 100
    days_over_90_percentage = (days_over_90 / total) * 100
    
    # Count customers with balance
    customers_with_balance = sum(1 for data in customer_balances.values() if data['total_due'] > 0)
    
    # Calculate overdue receivable
    overdue_receivable = days_1_30 + days_31_60 + days_61_90 + days_over_90
    
    return render_template('reports/accounts_receivable.html',
                           customer_balances=customer_balances,
                           outstanding_orders=outstanding_orders,
                           total_receivable=total_receivable,
                           current_receivable=current_receivable,
                           days_1_30=days_1_30,
                           days_31_60=days_31_60,
                           days_61_90=days_61_90,
                           days_over_90=days_over_90,
                           current_percentage=current_percentage,
                           days_1_30_percentage=days_1_30_percentage,
                           days_31_60_percentage=days_31_60_percentage,
                           days_61_90_percentage=days_61_90_percentage,
                           days_over_90_percentage=days_over_90_percentage,
                           customers_with_balance=customers_with_balance,
                           overdue_receivable=overdue_receivable)

@app.route('/api/send-payment-reminder', methods=['POST'])
@login_required
def send_payment_reminder():
    """Send payment reminder email to customer"""
    customer_id = request.form.get('customer_id')
    subject = request.form.get('subject')
    message = request.form.get('message')
    
    if not customer_id or not subject or not message:
        flash('Missing required fields', 'danger')
        return redirect(url_for('reports_accounts_receivable'))
    
    customer = Customer.query.get_or_404(customer_id)
    
    # Send email
    try:
        from email_service import send_email
        
        success = send_email(
            recipient_email=customer.email,
            subject=subject,
            message_body=message,
            sender_name="Print Shop",
        )
        
        if success:
            flash(f'Payment reminder sent to {customer.name}', 'success')
        else:
            flash('Failed to send payment reminder', 'danger')
            
    except Exception as e:
        flash(f'Error sending payment reminder: {str(e)}', 'danger')
    
    return redirect(url_for('reports_accounts_receivable'))

# Order Pickup Routes
@app.route('/orders/<int:order_id>/pickup')
@login_required
def order_pickup(order_id):
    from flask_wtf import FlaskForm
    
    # Create a simple form for CSRF protection
    class PickupForm(FlaskForm):
        pass
        
    order = Order.query.get_or_404(order_id)
    form = PickupForm()
    return render_template('orders/pickup.html', order=order, form=form)

@app.route('/orders/<int:order_id>/pickup/process', methods=['POST'])
@login_required
def process_order_pickup(order_id):
    from flask_wtf import FlaskForm
    import base64
    import traceback
    
    # Create a form for CSRF validation
    class PickupForm(FlaskForm):
        pass
    
    form = PickupForm()
    if not form.validate_on_submit():
        flash('Invalid form submission. CSRF token missing or invalid.', 'danger')
        return redirect(url_for('order_pickup', order_id=order_id))
    
    order = Order.query.get_or_404(order_id)
    
    try:
        # Get form data
        pickup_by = request.form.get('pickup_by')
        signature_data = request.form.get('signature-data')  # Match HTML field name
        signature_name = request.form.get('signature_name')
        print_receipt = request.form.get('print_receipt') == '1'
        
        # Enhanced logging for debugging
        app.logger.debug(f"Form data received for order #{order_id}:")
        app.logger.debug(f"- Pickup by: {pickup_by}")
        app.logger.debug(f"- Signature name: {signature_name}")
        app.logger.debug(f"- Signature data present: {bool(signature_data)}")
        app.logger.debug(f"- Print receipt: {print_receipt}")
        
        # Validate required fields
        errors = []
        if not pickup_by:
            errors.append("Pickup by name is required")
        if not signature_data:
            errors.append("Signature data is missing")
        if not signature_name:
            errors.append("Signature name is required")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
                app.logger.error(f"Validation error: {error}")
            return redirect(url_for('order_pickup', order_id=order_id))
        
        # Check if the signature data is valid
        if not signature_data.startswith('data:'):
            flash("Invalid signature data format. Please try again.", 'danger')
            app.logger.error(f"Invalid signature data format for order #{order_id}")
            return redirect(url_for('order_pickup', order_id=order_id))
        
        # Determine if this is a signature or photo based on the data URL
        is_photo = "data:image/png" in signature_data and not ",AAAASUVO" in signature_data
        confirmation_method = "photo" if is_photo else "signature"
        
        app.logger.debug(f"Confirmation method detected: {confirmation_method}")
        
        # Update order with pickup information
        order.is_picked_up = True
        order.pickup_date = datetime.utcnow()
        order.pickup_by = pickup_by
        order.pickup_signature = signature_data
        order.pickup_signature_name = signature_name
        
        # Create activity entry
        activity = OrderActivity(
            order_id=order.id,
            user_id=current_user.id,
            activity_type='order_pickup',
            description=f'Order picked up by {pickup_by} (confirmed via {confirmation_method})'
        )
        
        db.session.add(activity)
        db.session.commit()
        
        app.logger.info(f"Order #{order_id} pickup recorded successfully with {confirmation_method} confirmation")
        
        flash(f'Order pickup recorded successfully. Confirmation method: {confirmation_method}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error processing order #{order_id} pickup: {str(e)}")
        app.logger.error(traceback.format_exc())
        flash(f'An error occurred while processing the pickup: {str(e)}', 'danger')
        return redirect(url_for('order_pickup', order_id=order_id))
    
    # Handle receipt printing if requested
    if print_receipt:
        # Generate a receipt PDF with the signature
        try:
            receipt_file = generate_pickup_receipt(order)
            flash(f'Receipt generated successfully. <a href="{url_for("files_download", file_id=receipt_file.id)}" class="alert-link">Download Receipt</a>', 'success')
        except Exception as e:
            app.logger.error(f"Error generating receipt: {str(e)}")
            flash(f'Error generating receipt: {str(e)}', 'warning')
    
    flash(f'Order {order.order_number} marked as picked up by {pickup_by}.', 'success')
    return redirect(url_for('orders_view', id=order_id))

# Note: QR code and tracking routes have been moved to routes_addon.py
# The functions are:
# - order_qr_code at /order/qrcode/<int:order_id>
# - track_order at /track/<tracking_code>