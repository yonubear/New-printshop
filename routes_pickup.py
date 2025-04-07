"""
Basic Order Pickup Routes

Provides simplified routes for order pickup with basic signature and photo capture.
"""

import base64
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_wtf import FlaskForm
from models import db, Order, OrderFile
import pdf_generator

# Create blueprint
basic_pickup_bp = Blueprint('basic_pickup', __name__)

# Form for CSRF protection
class PickupForm(FlaskForm):
    pass

@basic_pickup_bp.route('/orders/<int:order_id>/basic-pickup', methods=['GET'])
def basic_pickup(order_id):
    """Show the basic order pickup page"""
    order = Order.query.get_or_404(order_id)
    form = PickupForm()
    return render_template('orders/basic_pickup.html', order=order, form=form)

@basic_pickup_bp.route('/orders/<int:order_id>/process-basic-pickup', methods=['POST'])
def process_basic_pickup(order_id):
    """Process the order pickup form submission"""
    order = Order.query.get_or_404(order_id)
    form = PickupForm()
    
    if not form.validate_on_submit():
        flash('Error validating form. Please try again.', 'danger')
        return redirect(url_for('basic_pickup.basic_pickup', order_id=order_id))
    
    try:
        # Get form data
        pickup_by = request.form.get('pickup_by', '')
        signature_data = request.form.get('signature-data', '')
        print_receipt = 'print_receipt' in request.form
        
        # Ensure we have data
        if not signature_data or not pickup_by:
            flash('Missing required information. Please provide a name and signature.', 'danger')
            return redirect(url_for('basic_pickup.basic_pickup', order_id=order_id))
        
        # Save signature data
        if signature_data:
            # Strip data URI prefix if present
            if signature_data.startswith('data:image/png;base64,'):
                signature_data = signature_data[22:]
            
            # Create a unique filename
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f'signature_{order.id}_{timestamp}.png'
            
            # Save to uploads directory
            uploads_dir = os.path.join(current_app.static_folder, 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            filepath = os.path.join(uploads_dir, filename)
            
            # Write signature file
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(signature_data))
            
            # Create order file record
            order_file = OrderFile(
                order_id=order.id,
                filename=filename,
                filepath=f'/static/uploads/{filename}',
                filetype='signature',
                description=f'Pickup signature by {pickup_by}',
                is_proof=False
            )
            db.session.add(order_file)
        
        # Update order status
        order.status = 'Completed'
        order.pickup_by = pickup_by
        order.pickup_date = datetime.now()
        
        # Commit changes
        db.session.commit()
        
        # Generate receipt if requested
        if print_receipt:
            pdf_url = pdf_generator.generate_pickup_receipt(order.id)
            flash(f'Pickup receipt generated. <a href="{pdf_url}" target="_blank">View Receipt</a>', 'success')
        
        flash(f'Order #{order.order_number} marked as picked up by {pickup_by}.', 'success')
        return redirect(url_for('orders_view', id=order.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing pickup: {str(e)}', 'danger')
        current_app.logger.error(f'Error processing pickup: {str(e)}')
        return redirect(url_for('basic_pickup.basic_pickup', order_id=order_id))