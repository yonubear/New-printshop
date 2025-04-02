import os
import uuid
import logging
import functools
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort, g
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app import app, db
from models import User, Customer, Order, OrderItem, ItemMaterial, OrderFile, OrderActivity, SavedPrice, SavedPriceMaterial, Quote, QuoteItem, FinishingOption, PaperOption, PrintPricing
from nextcloud_client import NextcloudClient
from pdf_generator import generate_order_form, generate_pull_sheet, generate_quote_pdf
from email_service import send_proof_approval_email

# Mock the login_required decorator to do nothing
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

# Initialize Nextcloud client if configs are available
if app.config['NEXTCLOUD_URL'] and app.config['NEXTCLOUD_USERNAME'] and app.config['NEXTCLOUD_PASSWORD']:
    nextcloud = NextcloudClient(
        app.config['NEXTCLOUD_URL'],
        app.config['NEXTCLOUD_USERNAME'],
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
        return g.user.id if g.user else 1
    
    @property
    def is_authenticated(self):
        return True

# Create a global instance
current_user = CurrentUser()

# Setup default admin user for all requests (since we've removed authentication)
@app.before_request
def get_default_user():
    # Set a global admin user for the whole application
    # This simulates being logged in without requiring actual authentication
    g.user = User.query.filter_by(role='admin').first()
    
    # If no admin exists yet, create one
    if not g.user:
        default_admin = User(
            username="admin",
            email="admin@example.com",
            role="admin"
        )
        default_admin.set_password("password123")
        db.session.add(default_admin)
        db.session.commit()
        g.user = default_admin
        app.logger.info("Created default admin user")

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
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        address = request.form.get('address')
        notes = request.form.get('notes')
        
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            company=company,
            address=address,
            notes=notes
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash(f'Customer {name} created successfully', 'success')
        return redirect(url_for('customers_index'))
    
    return render_template('customers/create.html')

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def customers_edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.company = request.form.get('company')
        customer.address = request.form.get('address')
        customer.notes = request.form.get('notes')
        
        db.session.commit()
        
        flash(f'Customer {customer.name} updated successfully', 'success')
        return redirect(url_for('customers_index'))
    
    return render_template('customers/edit.html', customer=customer)

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
    customers = Customer.query.order_by(Customer.name).all()
    
    if request.method == 'POST':
        # Get custom order number or generate a unique one
        custom_order_number = request.form.get('order_number')
        
        if custom_order_number and custom_order_number.strip():
            order_number = custom_order_number.strip()
        else:
            # Generate a unique order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
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
    
    return render_template('orders/create.html', customers=customers)

@app.route('/orders/<int:id>')
@login_required
def orders_view(id):
    order = Order.query.get_or_404(id)
    activities = OrderActivity.query.filter_by(order_id=id).order_by(OrderActivity.created_at.desc()).all()
    
    return render_template('orders/view.html', order=order, activities=activities)

@app.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def orders_edit(id):
    order = Order.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    
    if request.method == 'POST':
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
    
    return render_template('orders/edit.html', order=order, customers=customers, saved_materials=saved_materials)

# Order items routes
@app.route('/orders/<int:order_id>/items/add', methods=['POST'])
@login_required
def order_items_add(order_id):
    order = Order.query.get_or_404(order_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    sku = request.form.get('sku')
    quantity = int(request.form.get('quantity', 1))
    unit_price = float(request.form.get('unit_price', 0.0))
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

@app.route('/orders/items/<int:item_id>/edit', methods=['POST'])
@login_required
def order_items_edit(item_id):
    item = OrderItem.query.get_or_404(item_id)
    order = item.order
    
    item.name = request.form.get('name')
    item.description = request.form.get('description')
    item.sku = request.form.get('sku')
    item.quantity = int(request.form.get('quantity', 1))
    item.unit_price = float(request.form.get('unit_price', 0.0))
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
    item = OrderItem.query.get_or_404(item_id)
    
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

@app.route('/item-materials/<int:material_id>/edit', methods=['POST'])
@login_required
def item_materials_edit(material_id):
    material = ItemMaterial.query.get_or_404(material_id)
    item = OrderItem.query.get_or_404(material.order_item_id)
    
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

@app.route('/item-materials/<int:material_id>/delete', methods=['POST'])
@login_required
def item_materials_delete(material_id):
    material = ItemMaterial.query.get_or_404(material_id)
    item = OrderItem.query.get_or_404(material.order_item_id)
    material_name = material.material_name
    
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

# File management routes
@app.route('/orders/<int:order_id>/files')
@login_required
def order_files_index(order_id):
    order = Order.query.get_or_404(order_id)
    files = OrderFile.query.filter_by(order_id=order_id).all()
    
    return render_template('files/index.html', order=order, files=files)

@app.route('/orders/<int:order_id>/files/upload', methods=['GET', 'POST'])
@login_required
def order_files_upload(order_id):
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
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
    
    return render_template('files/upload.html', order=order)

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
    order_file = OrderFile.query.get_or_404(file_id)
    order_id = order_file.order_id
    
    # Delete file from Nextcloud
    success = nextcloud.delete_file(order_file.file_path)
    
    if success:
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
        flash('Failed to delete file from Nextcloud', 'danger')
    
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
    order = Order.query.get_or_404(order_id)
    
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
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

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
    if request.method == 'POST':
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
            
            # For template material approach with JavaScript
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            
            # Process template materials
            for i in range(len(template_material_ids)):
                if not template_material_ids[i]:  # Skip empty entries
                    continue
                    
                # Get the corresponding saved price (material) record
                material_id = int(template_material_ids[i])
                material_price = SavedPrice.query.get(material_id)
                
                if not material_price:
                    continue
                    
                # Get quantity
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) and template_material_quantities[i] else 1
                
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
            
            db.session.commit()
        
        flash(f'Price item "{name}" created successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
    # Get all material type prices for the materials dropdown
    materials = SavedPrice.query.filter(
        (SavedPrice.category == 'material') | 
        (SavedPrice.category == 'paper')
    ).order_by(SavedPrice.name).all()
    
    return render_template('saved_prices/create.html', materials=materials)

@app.route('/saved-prices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def saved_prices_edit(id):
    saved_price = SavedPrice.query.get_or_404(id)
    
    if request.method == 'POST':
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
            
            # Remove all existing materials
            SavedPriceMaterial.query.filter_by(saved_price_id=id).delete()
            
            # Add new materials from form
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            
            # Process template materials
            for i in range(len(template_material_ids)):
                if not template_material_ids[i]:  # Skip empty entries
                    continue
                    
                # Get the corresponding saved price (material) record
                material_id = int(template_material_ids[i])
                material_price = SavedPrice.query.get(material_id)
                
                if not material_price:
                    continue
                    
                # Get quantity
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) and template_material_quantities[i] else 1
                
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
        
        # Save changes
        db.session.commit()
        
        flash(f'Price item "{saved_price.name}" updated successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
    # Get all material type prices for the materials dropdown
    materials = SavedPrice.query.filter(
        (SavedPrice.category == 'material') | 
        (SavedPrice.category == 'paper')
    ).order_by(SavedPrice.name).all()
    
    # Get existing template materials
    template_materials = []
    if saved_price.is_template:
        for tm in saved_price.materials:
            # Try to find the linked material by name
            linked_material = SavedPrice.query.filter_by(name=tm.material_name).first()
            material_id = linked_material.id if linked_material else 0
            
            template_materials.append({
                'material_id': material_id,
                'material_name': tm.material_name,
                'quantity': tm.quantity
            })
    
    return render_template('saved_prices/edit.html', 
                          saved_price=saved_price, 
                          materials=materials, 
                          template_materials=template_materials)

@app.route('/saved-prices/<int:id>/delete', methods=['POST'])
@login_required
def saved_prices_delete(id):
    saved_price = SavedPrice.query.get_or_404(id)
    name = saved_price.name
    
    db.session.delete(saved_price)
    db.session.commit()
    
    flash(f'Price item "{name}" deleted successfully', 'success')
    return redirect(url_for('saved_prices_index'))

@app.route('/saved_prices/import', methods=['GET', 'POST'])
@login_required
def saved_prices_import():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'excel_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['excel_file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename, ['xlsx', 'xls']):
            try:
                # Import data from Excel
                import pandas as pd
                
                # Read Excel file
                df = pd.read_excel(file)
                
                # Define required columns
                required_columns = ['name', 'category', 'price']
                
                # Check if all required columns exist
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    flash(f"Missing required columns: {', '.join(missing_columns)}. Please check the Excel template.", 'danger')
                    return redirect(request.url)
                
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
                
                if error_count > 0:
                    flash(f'Imported {success_count} items successfully with {error_count} errors.', 'warning')
                else:
                    flash(f'Successfully imported {success_count} items.', 'success')
                
                return redirect(url_for('saved_prices_index'))
            
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('saved_prices/import.html')

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

# API to retrieve saved prices for order form
@app.route('/api/saved-prices', methods=['GET'])
@login_required
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
@login_required
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
    customers = Customer.query.order_by(Customer.name).all()
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    if request.method == 'POST':
        # Get custom quote number or generate a unique one
        custom_quote_number = request.form.get('quote_number')
        
        if custom_quote_number and custom_quote_number.strip():
            quote_number = custom_quote_number.strip()
        else:
            # Generate a unique quote number
            quote_number = f"QTE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        customer_id = request.form.get('customer_id')
        title = request.form.get('title')
        description = request.form.get('description')
        valid_until_str = request.form.get('valid_until')
        
        # Parse valid until date if provided
        valid_until = None
        if valid_until_str:
            valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')
            
        # Default user ID to 1 since we're not using authentication
        quote = Quote(
            quote_number=quote_number,
            customer_id=customer_id,
            user_id=1,  # Using the default admin user
            title=title,
            description=description,
            valid_until=valid_until,
            status='draft'
        )
        
        db.session.add(quote)
        db.session.commit()
        
        flash(f'Quote {quote.quote_number} created successfully. Add items to it.', 'success')
        return redirect(url_for('quotes_edit', id=quote.id))
    
    return render_template('quotes/create.html', 
                          customers=customers, 
                          paper_options=paper_options,
                          finishing_options=finishing_options)

@app.route('/quotes/<int:id>', methods=['GET', 'POST'])
def quotes_view(id):
    quote = Quote.query.get_or_404(id)
    
    # Handle status updates
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_status':
            new_status = request.form.get('status')
            if new_status in ['draft', 'sent', 'accepted', 'declined', 'expired']:
                quote.status = new_status
                db.session.commit()
                flash(f'Quote status updated to {new_status}', 'success')
                return redirect(url_for('quotes_view', id=quote.id))
    
    # Handle conversion to order
    if request.args.get('convert_to_order') == '1':
        # TODO: Implement conversion to order functionality
        flash('Converting to order functionality is coming soon', 'info')
        return redirect(url_for('quotes_view', id=quote.id))
    
    return render_template('quotes/view.html', quote=quote)

@app.route('/quotes/<int:id>/edit', methods=['GET', 'POST'])
def quotes_edit(id):
    quote = Quote.query.get_or_404(id)
    customers = Customer.query.order_by(Customer.name).all()
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    if request.method == 'POST':
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
                          customers=customers,
                          paper_options=paper_options,
                          finishing_options=finishing_options)

@app.route('/quotes/<int:id>/delete', methods=['POST'])
def quotes_delete(id):
    quote = Quote.query.get_or_404(id)
    quote_number = quote.quote_number
    
    db.session.delete(quote)
    db.session.commit()
    
    flash(f'Quote {quote_number} deleted successfully', 'success')
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

# Quote items routes
@app.route('/quotes/<int:quote_id>/items/add', methods=['POST'])
def quote_items_add(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    sku = request.form.get('sku')
    
    # Get print specifications
    size = request.form.get('size')
    custom_width = request.form.get('custom_width')
    custom_height = request.form.get('custom_height')
    finish_size = request.form.get('finish_size')
    color_type = request.form.get('color_type')
    sides = request.form.get('sides')
    paper_type = request.form.get('paper_type')
    paper_weight = request.form.get('paper_weight')
    
    # Get finishing options and calculate their costs
    finishing_option_list = request.form.getlist('finishing_options')
    finishing_options = ','.join(finishing_option_list)
    
    quantity = int(request.form.get('quantity', 1))
    unit_price = float(request.form.get('unit_price', 0.0))
    
    # Calculate base price without finishing options
    base_price = quantity * unit_price
    
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
                    option_cost += option.price_per_piece * quantity
                
                # For future: add per-sqft calculations if needed
                
                # Apply minimum price if needed
                if option.minimum_price > 0 and option_cost < option.minimum_price:
                    option_cost = option.minimum_price
                
                # Add to total finishing cost
                finishing_cost += option_cost
    
    # Calculate total price including finishing costs
    total_price = base_price + finishing_cost
    
    # Get product type and booklet-specific fields
    product_type = request.form.get('product_type', 'print_job')
    
    # Get booklet fields if this is a booklet
    page_count = None
    cover_paper_type = None
    binding_type = None
    cover_printing = None
    self_cover = False
    
    if product_type == 'booklet':
        page_count = request.form.get('page_count')
        if page_count:
            page_count = int(page_count)
        cover_paper_type = request.form.get('cover_paper_type')
        binding_type = request.form.get('binding_type')
        cover_printing = request.form.get('cover_printing')
        self_cover = request.form.get('self_cover') == 'on'
    
    item = QuoteItem(
        quote_id=quote.id,
        name=name,
        description=description,
        sku=sku,
        product_type=product_type,
        page_count=page_count,
        cover_paper_type=cover_paper_type,
        binding_type=binding_type,
        cover_printing=cover_printing,
        self_cover=self_cover,
        size=size,
        custom_width=custom_width if custom_width else None,
        custom_height=custom_height if custom_height else None,
        finish_size=finish_size,
        color_type=color_type,
        sides=sides,
        paper_type=paper_type,
        paper_weight=paper_weight,
        finishing_options=finishing_options,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price
    )
    
    db.session.add(item)
    
    # Update quote total
    quote.total_price = sum(item.total_price for item in quote.items) + total_price
    
    db.session.commit()
    
    flash(f'Item added to quote successfully', 'success')
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quotes/items/<int:item_id>/edit', methods=['POST'])
def quote_items_edit(item_id):
    item = QuoteItem.query.get_or_404(item_id)
    quote = item.quote
    
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
    item.total_price = base_price + finishing_cost
    
    # Update quote total
    quote.total_price = sum(i.total_price for i in quote.items)
    
    db.session.commit()
    
    flash(f'Item updated successfully', 'success')
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quotes/items/<int:item_id>/delete', methods=['POST'])
def quote_items_delete(item_id):
    item = QuoteItem.query.get_or_404(item_id)
    quote = item.quote
    
    item_name = item.name
    
    db.session.delete(item)
    
    # Update quote total
    quote.total_price = sum(i.total_price for i in quote.items if i.id != item_id)
    
    db.session.commit()
    
    flash(f'Item removed from quote successfully', 'success')
    return redirect(url_for('quotes_edit', id=quote.id))

# API routes for paper and finishing options
@app.route('/api/paper-options', methods=['GET'])
def api_paper_options():
    size = request.args.get('size')
    weight = request.args.get('weight')
    paper_id = request.args.get('paper_id')
    
    query = PaperOption.query
    
    # If we have a specific paper ID, just get that paper
    if paper_id:
        try:
            paper_id = int(paper_id)
            paper = PaperOption.query.get(paper_id)
            if paper:
                # Return just this one paper
                return jsonify([{
                    'id': paper.id,
                    'name': paper.name,
                    'description': paper.description,
                    'category': paper.category,
                    'weight': paper.weight,
                    'size': paper.size,
                    'color': paper.color,
                    'price_per_sheet': paper.price_per_sheet
                }])
        except (ValueError, TypeError):
            # Invalid paper ID, continue with regular filtering
            pass
    
    # Apply filters if provided
    if size and size != 'Custom':
        # Map standard sizes to database format
        size_mapping = {
            'Letter (8.5x11)': 'Letter',
            'Legal (8.5x14)': 'Legal',
            'Tabloid (11x17)': 'Tabloid',
            '12x18': '12x18',
            '13x19': '13x19'
        }
        
        db_size = size_mapping.get(size, size)
        query = query.filter(PaperOption.size == db_size)
    
    if weight:
        # Handle multiple weight formats:
        # 1. Extract the base weight (e.g., "100# Cover" -> "100#")
        base_weight = weight.split(' ')[0] if ' ' in weight else weight
        
        # 2. Also check for exact match (for legacy data)
        query = query.filter(
            db.or_(
                PaperOption.weight == base_weight,
                PaperOption.weight == weight
            )
        )
    
    # Order by name
    paper_options = query.order_by(PaperOption.category, PaperOption.name).all()
    
    result = []
    for option in paper_options:
        result.append({
            'id': option.id,
            'name': option.name,
            'description': option.description,
            'category': option.category,
            'weight': option.weight,
            'size': option.size,
            'color': option.color,
            'price_per_sheet': option.price_per_sheet
        })
    
    return jsonify(result)

@app.route('/api/print-pricing', methods=['GET'])
def api_print_pricing():
    paper_size = request.args.get('paper_size')
    color_type = request.args.get('color_type')
    
    # Check if we have both parameters
    if not paper_size or not color_type:
        return jsonify({'error': 'Missing parameters. Please provide paper_size and color_type.'}), 400
    
    # Try to find an exact match first
    pricing = PrintPricing.query.filter_by(paper_size=paper_size, color_type=color_type).first()
    
    if not pricing:
        # If no exact match, try to find a generic one (e.g., "Any" size)
        pricing = PrintPricing.query.filter_by(color_type=color_type).filter(PrintPricing.paper_size.in_(['Any', 'Universal'])).first()
    
    if not pricing:
        return jsonify({'error': 'No pricing configuration found for the specified combination.'}), 404
    
    return jsonify({
        'id': pricing.id,
        'name': pricing.name,
        'paper_size': pricing.paper_size,
        'color_type': pricing.color_type,
        'price_per_side': pricing.price_per_side,
        'cost_per_side': pricing.cost_per_side
    })

@app.route('/api/finishing-options', methods=['GET'])
def api_finishing_options():
    finishing_options = FinishingOption.query.order_by(FinishingOption.category, FinishingOption.name).all()
    
    result = []
    for option in finishing_options:
        result.append({
            'id': option.id,
            'name': option.name,
            'description': option.description,
            'category': option.category,
            'base_price': option.base_price,
            'price_per_piece': option.price_per_piece,
            'price_per_sqft': option.price_per_sqft,
            'minimum_price': option.minimum_price
        })
    
    return jsonify(result)

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
        notes = request.form.get('notes')
        
        pricing = PrintPricing(
            name=name,
            paper_size=paper_size,
            color_type=color_type,
            price_per_side=price_per_side,
            cost_per_side=cost_per_side,
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
        
        paper_option = PaperOption(
            name=name,
            description=description,
            category=category,
            weight=weight,
            size=size,
            color=color,
            price_per_sheet=price_per_sheet
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
        
        db.session.commit()
        
        flash(f'Paper option "{paper_option.name}" updated successfully', 'success')
        return redirect(url_for('paper_options_index'))
    
    return render_template('paper_options/edit.html', paper_option=paper_option)

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
