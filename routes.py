import os
import uuid
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import text
from app import app, db
from models import User, Customer, Order, OrderItem, ItemMaterial, OrderFile, OrderActivity, SavedPrice, SavedPriceMaterial, Quote, QuoteItem, FinishingOption, PaperOption
from nextcloud_client import NextcloudClient
from pdf_generator import generate_order_form, generate_pull_sheet, generate_quote_pdf
from email_service import send_proof_approval_email

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

# Import Flask-WTF Form class
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

# Create login form class
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # Log successful login
            app.logger.info(f"Successful login for user: {username}")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            app.logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
    
    return render_template('orders/edit.html', order=order, customers=customers)

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
    
    # Add materials if available
    if material_names and len(material_names) > 0:
        for i in range(len(material_names)):
            if not material_names[i]:
                continue
                
            material = ItemMaterial(
                order_item_id=item.id,
                material_name=material_names[i],
                quantity=float(material_quantities[i]) if i < len(material_quantities) and material_quantities[i] else 0,
                unit=material_units[i] if i < len(material_units) and material_units[i] else 'pcs',
                notes=material_notes[i] if i < len(material_notes) and material_notes[i] else ''
            )
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
    
    material_name = request.form.get('material_name')
    quantity = float(request.form.get('quantity', 0.0))
    unit = request.form.get('unit')
    notes = request.form.get('notes')
    
    material = ItemMaterial(
        order_item_id=item.id,
        material_name=material_name,
        quantity=quantity,
        unit=unit,
        notes=notes
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
        name = request.form.get('name')
        description = request.form.get('description')
        sku = request.form.get('sku')
        category = request.form.get('category')
        cost_price = float(request.form.get('cost_price', 0.0))
        price = float(request.form.get('price', 0.0))
        unit = request.form.get('unit')
        is_template = 'is_template' in request.form
        
        # Create new saved price
        saved_price = SavedPrice(
            name=name,
            description=description,
            sku=sku,
            category=category,
            cost_price=cost_price,
            price=price,
            unit=unit,
            is_template=is_template
        )
        
        db.session.add(saved_price)
        db.session.commit()
        
        # Handle materials if this is a template
        if is_template:
            material_names = request.form.getlist('material_names[]')
            material_quantities = request.form.getlist('material_quantities[]')
            material_units = request.form.getlist('material_units[]')
            material_costs = request.form.getlist('material_costs[]')
            material_notes = request.form.getlist('material_notes[]')
            material_categories = request.form.getlist('material_categories[]')
            
            # Create materials for this template
            for i in range(len(material_names)):
                if material_names[i].strip():  # Only add if material name is not empty
                    material = SavedPriceMaterial(
                        saved_price_id=saved_price.id,
                        material_name=material_names[i],
                        quantity=float(material_quantities[i] if material_quantities[i] else 0),
                        unit=material_units[i],
                        cost_price=float(material_costs[i] if material_costs[i] else 0),
                        notes=material_notes[i] if i < len(material_notes) else None,
                        category=material_categories[i] if i < len(material_categories) else 'other'
                    )
                    db.session.add(material)
            
            db.session.commit()
        
        flash(f'Price item "{name}" created successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
    return render_template('saved_prices/create.html')

@app.route('/saved-prices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def saved_prices_edit(id):
    saved_price = SavedPrice.query.get_or_404(id)
    
    # Get all material items (for templates)
    materials = SavedPrice.query.filter_by(category='material').order_by(SavedPrice.name).all()
    
    # Get existing template materials if this is a template
    template_materials = []
    if saved_price.is_template:
        # Get materials linked to this template from the linking table
        material_links = db.session.execute(text("""
            SELECT l.id, l.material_id, l.quantity, s.name, s.unit
            FROM saved_price_material_link l
            JOIN saved_price s ON l.material_id = s.id
            WHERE l.template_id = :template_id
        """), {"template_id": saved_price.id}).fetchall()
        
        for link in material_links:
            template_materials.append({
                'id': link.id,
                'material_id': link.material_id,
                'material_name': link.name,
                'quantity': link.quantity,
                'unit': link.unit
            })
    
    if request.method == 'POST':
        saved_price.name = request.form.get('name')
        saved_price.description = request.form.get('description')
        saved_price.sku = request.form.get('sku')
        saved_price.category = request.form.get('category')
        saved_price.cost_price = float(request.form.get('cost_price', 0.0))
        saved_price.price = float(request.form.get('price', 0.0))
        saved_price.unit = request.form.get('unit')
        saved_price.is_template = 'is_template' in request.form
        
        # Handle template materials if this is a template
        if saved_price.is_template:
            # Get materials from the form
            material_ids = request.form.getlist('template_material_ids[]')
            material_quantities = request.form.getlist('template_material_quantities[]')
            
            # Delete all existing template material links
            db.session.execute(text("""
                DELETE FROM saved_price_material_link
                WHERE template_id = :template_id
            """), {"template_id": saved_price.id})
            
            # Add new template material links
            for i in range(len(material_ids)):
                if not material_ids[i]:
                    continue
                
                # Get the material (SavedPrice with category='material')
                material_id = int(material_ids[i])
                material_price = SavedPrice.query.get(material_id)
                
                if not material_price or material_price.category != 'material':
                    continue
                
                quantity = float(material_quantities[i] if material_quantities[i] else 0)
                
                # Create a new link in the saved_price_material_link table
                db.session.execute(text("""
                    INSERT INTO saved_price_material_link (template_id, material_id, quantity)
                    VALUES (:template_id, :material_id, :quantity)
                """), {
                    "template_id": saved_price.id,
                    "material_id": material_id,
                    "quantity": quantity
                })
        else:
            # If not a template anymore, delete all material links
            db.session.execute(text("""
                DELETE FROM saved_price_material_link
                WHERE template_id = :template_id
            """), {"template_id": saved_price.id})
                
        db.session.commit()
        
        flash(f'Price item "{saved_price.name}" updated successfully', 'success')
        return redirect(url_for('saved_prices_index'))
    
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
            
        quote = Quote(
            quote_number=quote_number,
            customer_id=customer_id,
            user_id=current_user.id,
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
@login_required
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
@login_required
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
@login_required
def quotes_delete(id):
    quote = Quote.query.get_or_404(id)
    quote_number = quote.quote_number
    
    db.session.delete(quote)
    db.session.commit()
    
    flash(f'Quote {quote_number} deleted successfully', 'success')
    return redirect(url_for('quotes_index'))

# Quote PDF generation route
@app.route('/quotes/<int:id>/pdf')
@login_required
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
@login_required
def quote_items_add(quote_id):
    quote = Quote.query.get_or_404(quote_id)
    
    name = request.form.get('name')
    description = request.form.get('description')
    sku = request.form.get('sku')
    
    # Get print specifications
    size = request.form.get('size')
    custom_width = request.form.get('custom_width')
    custom_height = request.form.get('custom_height')
    color_type = request.form.get('color_type')
    sides = request.form.get('sides')
    paper_type = request.form.get('paper_type')
    paper_weight = request.form.get('paper_weight')
    
    # Get finishing options as comma-separated string
    finishing_options = ','.join(request.form.getlist('finishing_options'))
    
    quantity = int(request.form.get('quantity', 1))
    unit_price = float(request.form.get('unit_price', 0.0))
    total_price = quantity * unit_price
    
    item = QuoteItem(
        quote_id=quote.id,
        name=name,
        description=description,
        sku=sku,
        size=size,
        custom_width=custom_width if custom_width else None,
        custom_height=custom_height if custom_height else None,
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
@login_required
def quote_items_edit(item_id):
    item = QuoteItem.query.get_or_404(item_id)
    quote = item.quote
    
    item.name = request.form.get('name')
    item.description = request.form.get('description')
    item.sku = request.form.get('sku')
    
    # Update print specifications
    item.size = request.form.get('size')
    item.custom_width = request.form.get('custom_width')
    item.custom_height = request.form.get('custom_height')
    item.color_type = request.form.get('color_type')
    item.sides = request.form.get('sides')
    item.paper_type = request.form.get('paper_type')
    item.paper_weight = request.form.get('paper_weight')
    
    # Update finishing options
    item.finishing_options = ','.join(request.form.getlist('finishing_options'))
    
    item.quantity = int(request.form.get('quantity', 1))
    item.unit_price = float(request.form.get('unit_price', 0.0))
    item.total_price = item.quantity * item.unit_price
    
    # Update quote total
    quote.total_price = sum(i.total_price for i in quote.items)
    
    db.session.commit()
    
    flash(f'Item updated successfully', 'success')
    return redirect(url_for('quotes_edit', id=quote.id))

@app.route('/quotes/items/<int:item_id>/delete', methods=['POST'])
@login_required
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
@login_required
def api_paper_options():
    paper_options = PaperOption.query.order_by(PaperOption.category, PaperOption.name).all()
    
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

@app.route('/api/finishing-options', methods=['GET'])
@login_required
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
@login_required
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
            user_id=current_user.id,
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
