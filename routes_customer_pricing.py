"""
Customer-specific pricing routes for Print Order Management System
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, FloatField, BooleanField, DateField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional
from datetime import datetime, timedelta

from app import app, db
from models import Customer, SavedPrice, PaperOption, FinishingOption, PrintPricing, CustomerPrice

# Customer price management routes
@app.route('/customer-prices')
def customer_prices_index():
    """Display list of all customer prices"""
    customer_prices = CustomerPrice.query.order_by(CustomerPrice.customer_id, CustomerPrice.name).all()
    return render_template('customer_prices/index.html', 
                          customer_prices=customer_prices,
                          now=datetime.utcnow)

@app.route('/customer-prices/create', methods=['GET', 'POST'])
def customer_prices_create():
    """Create a new customer-specific price"""
    # Create a form for CSRF protection and validation
    class CustomerPriceForm(FlaskForm):
        customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
        name = StringField('Price Name', validators=[DataRequired()])
        description = TextAreaField('Description')
        
        # Price source options
        price_source = SelectField('Price Source', choices=[
            ('saved_price', 'Product or Service'),
            ('paper_option', 'Paper'),
            ('finishing_option', 'Finishing Option'),
            ('print_pricing', 'Print Pricing'),
            ('custom', 'Custom Price')
        ])
        
        # Reference IDs for various pricing sources
        saved_price_id = SelectField('Product or Service', coerce=int, validators=[Optional()])
        paper_option_id = SelectField('Paper', coerce=int, validators=[Optional()])
        finishing_option_id = SelectField('Finishing Option', coerce=int, validators=[Optional()])
        print_pricing_id = SelectField('Print Pricing', coerce=int, validators=[Optional()])
        
        # Custom price fields
        price = FloatField('Price', validators=[DataRequired()])
        
        # Discount fields
        discount_type = SelectField('Discount Type', choices=[
            ('percentage', 'Percentage (%)'),
            ('fixed', 'Fixed Amount ($)')
        ])
        discount_value = FloatField('Discount Value', default=0.0)
        
        # Validity period
        valid_from = DateField('Valid From', default=datetime.utcnow, validators=[DataRequired()])
        valid_until = DateField('Valid Until', validators=[Optional()])
        
        is_active = BooleanField('Active', default=True)
        notes = TextAreaField('Notes')
        
        submit = SubmitField('Create Custom Price')
    
    form = CustomerPriceForm()
    
    # Populate dropdown options
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by(Customer.name).all()]
    form.saved_price_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} (${p.price})") for p in SavedPrice.query.order_by(SavedPrice.name).all()]
    form.paper_option_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} {p.weight} (${p.price_per_sheet})") for p in PaperOption.query.order_by(PaperOption.name).all()]
    form.finishing_option_id.choices = [(0, '-- Select --')] + [(f.id, f"{f.name} (${f.base_price})") for f in FinishingOption.query.order_by(FinishingOption.name).all()]
    form.print_pricing_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} (${p.price_per_side})") for p in PrintPricing.query.order_by(PrintPricing.name).all()]
    
    if form.validate_on_submit():
        # Create new customer price record
        customer_price = CustomerPrice(
            customer_id=form.customer_id.data,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            valid_from=form.valid_from.data,
            valid_until=form.valid_until.data,
            is_active=form.is_active.data,
            notes=form.notes.data
        )
        
        # Set the appropriate ID based on selected price source
        if form.price_source.data == 'saved_price' and form.saved_price_id.data:
            customer_price.saved_price_id = form.saved_price_id.data if form.saved_price_id.data > 0 else None
        elif form.price_source.data == 'paper_option' and form.paper_option_id.data:
            customer_price.paper_option_id = form.paper_option_id.data if form.paper_option_id.data > 0 else None
        elif form.price_source.data == 'finishing_option' and form.finishing_option_id.data:
            customer_price.finishing_option_id = form.finishing_option_id.data if form.finishing_option_id.data > 0 else None
        elif form.price_source.data == 'print_pricing' and form.print_pricing_id.data:
            customer_price.print_pricing_id = form.print_pricing_id.data if form.print_pricing_id.data > 0 else None
        
        db.session.add(customer_price)
        db.session.commit()
        
        flash(f'Customer price "{customer_price.name}" created successfully', 'success')
        return redirect(url_for('customer_prices_index'))
    
    return render_template('customer_prices/create.html', form=form)

@app.route('/customer-prices/<int:id>/edit', methods=['GET', 'POST'])
def customer_prices_edit(id):
    """Edit an existing customer-specific price"""
    customer_price = CustomerPrice.query.get_or_404(id)
    
    # Create a form for CSRF protection and validation
    class CustomerPriceForm(FlaskForm):
        customer_id = SelectField('Customer', validators=[DataRequired()], coerce=int)
        name = StringField('Price Name', validators=[DataRequired()])
        description = TextAreaField('Description')
        
        # Price source options
        price_source = SelectField('Price Source', choices=[
            ('saved_price', 'Product or Service'),
            ('paper_option', 'Paper'),
            ('finishing_option', 'Finishing Option'),
            ('print_pricing', 'Print Pricing'),
            ('custom', 'Custom Price')
        ])
        
        # Reference IDs for various pricing sources
        saved_price_id = SelectField('Product or Service', coerce=int, validators=[Optional()])
        paper_option_id = SelectField('Paper', coerce=int, validators=[Optional()])
        finishing_option_id = SelectField('Finishing Option', coerce=int, validators=[Optional()])
        print_pricing_id = SelectField('Print Pricing', coerce=int, validators=[Optional()])
        
        # Custom price fields
        price = FloatField('Price', validators=[DataRequired()])
        
        # Discount fields
        discount_type = SelectField('Discount Type', choices=[
            ('percentage', 'Percentage (%)'),
            ('fixed', 'Fixed Amount ($)')
        ])
        discount_value = FloatField('Discount Value', default=0.0)
        
        # Validity period
        valid_from = DateField('Valid From', validators=[DataRequired()])
        valid_until = DateField('Valid Until', validators=[Optional()])
        
        is_active = BooleanField('Active', default=True)
        notes = TextAreaField('Notes')
        
        submit = SubmitField('Update Custom Price')
    
    form = CustomerPriceForm()
    
    # Populate dropdown options
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.order_by(Customer.name).all()]
    form.saved_price_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} (${p.price})") for p in SavedPrice.query.order_by(SavedPrice.name).all()]
    form.paper_option_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} {p.weight} (${p.price_per_sheet})") for p in PaperOption.query.order_by(PaperOption.name).all()]
    form.finishing_option_id.choices = [(0, '-- Select --')] + [(f.id, f"{f.name} (${f.base_price})") for f in FinishingOption.query.order_by(FinishingOption.name).all()]
    form.print_pricing_id.choices = [(0, '-- Select --')] + [(p.id, f"{p.name} (${p.price_per_side})") for p in PrintPricing.query.order_by(PrintPricing.name).all()]
    
    # Determine price source
    if customer_price.saved_price_id:
        price_source = 'saved_price'
    elif customer_price.paper_option_id:
        price_source = 'paper_option'
    elif customer_price.finishing_option_id:
        price_source = 'finishing_option'
    elif customer_price.print_pricing_id:
        price_source = 'print_pricing'
    else:
        price_source = 'custom'
    
    if request.method == 'GET':
        # Populate form with existing data
        form.customer_id.data = customer_price.customer_id
        form.name.data = customer_price.name
        form.description.data = customer_price.description
        form.price_source.data = price_source
        form.saved_price_id.data = customer_price.saved_price_id if customer_price.saved_price_id else 0
        form.paper_option_id.data = customer_price.paper_option_id if customer_price.paper_option_id else 0
        form.finishing_option_id.data = customer_price.finishing_option_id if customer_price.finishing_option_id else 0
        form.print_pricing_id.data = customer_price.print_pricing_id if customer_price.print_pricing_id else 0
        form.price.data = customer_price.price
        form.discount_type.data = customer_price.discount_type
        form.discount_value.data = customer_price.discount_value
        form.valid_from.data = customer_price.valid_from
        form.valid_until.data = customer_price.valid_until
        form.is_active.data = customer_price.is_active
        form.notes.data = customer_price.notes
    
    if form.validate_on_submit():
        # Update customer price record
        customer_price.customer_id = form.customer_id.data
        customer_price.name = form.name.data
        customer_price.description = form.description.data
        customer_price.price = form.price.data
        customer_price.discount_type = form.discount_type.data
        customer_price.discount_value = form.discount_value.data
        customer_price.valid_from = form.valid_from.data
        customer_price.valid_until = form.valid_until.data
        customer_price.is_active = form.is_active.data
        customer_price.notes = form.notes.data
        
        # Reset all reference IDs
        customer_price.saved_price_id = None
        customer_price.paper_option_id = None
        customer_price.finishing_option_id = None
        customer_price.print_pricing_id = None
        
        # Set the appropriate ID based on selected price source
        if form.price_source.data == 'saved_price' and form.saved_price_id.data:
            customer_price.saved_price_id = form.saved_price_id.data if form.saved_price_id.data > 0 else None
        elif form.price_source.data == 'paper_option' and form.paper_option_id.data:
            customer_price.paper_option_id = form.paper_option_id.data if form.paper_option_id.data > 0 else None
        elif form.price_source.data == 'finishing_option' and form.finishing_option_id.data:
            customer_price.finishing_option_id = form.finishing_option_id.data if form.finishing_option_id.data > 0 else None
        elif form.price_source.data == 'print_pricing' and form.print_pricing_id.data:
            customer_price.print_pricing_id = form.print_pricing_id.data if form.print_pricing_id.data > 0 else None
        
        db.session.commit()
        
        flash(f'Customer price "{customer_price.name}" updated successfully', 'success')
        return redirect(url_for('customer_prices_index'))
    
    return render_template('customer_prices/edit.html', form=form, customer_price=customer_price)

@app.route('/customer-prices/<int:id>/delete', methods=['POST'])
def customer_prices_delete(id):
    """Delete a customer-specific price"""
    from flask_wtf import FlaskForm
    
    form = FlaskForm()
    if form.validate_on_submit():
        customer_price = CustomerPrice.query.get_or_404(id)
        name = customer_price.name
        
        db.session.delete(customer_price)
        db.session.commit()
        
        flash(f'Customer price "{name}" deleted successfully', 'success')
    else:
        flash('CSRF token missing or invalid', 'danger')
        
    return redirect(url_for('customer_prices_index'))

@app.route('/customer-prices/customer/<int:customer_id>')
def customer_prices_by_customer(customer_id):
    """Display list of custom prices for a specific customer"""
    customer = Customer.query.get_or_404(customer_id)
    customer_prices = CustomerPrice.query.filter_by(customer_id=customer_id).all()
    
    return render_template('customer_prices/customer.html', 
                          customer=customer,
                          customer_prices=customer_prices,
                          now=datetime.utcnow)

@app.route('/api/customer-prices/<int:customer_id>')
def api_customer_prices(customer_id):
    """API endpoint to get customer prices for a specific customer"""
    customer_prices = CustomerPrice.query.filter_by(
        customer_id=customer_id, 
        is_active=True
    ).all()
    
    # Only include prices that are currently valid
    valid_prices = [cp for cp in customer_prices if cp.is_valid]
    
    result = []
    for cp in valid_prices:
        price_data = {
            'id': cp.id,
            'name': cp.name,
            'description': cp.description,
            'price': cp.price,
            'effective_price': cp.effective_price,
            'discount_type': cp.discount_type,
            'discount_value': cp.discount_value
        }
        
        # Add reference information depending on price type
        if cp.saved_price_id:
            price_data['price_type'] = 'saved_price'
            price_data['saved_price_id'] = cp.saved_price_id
            price_data['saved_price_name'] = cp.saved_price.name if cp.saved_price else None
        elif cp.paper_option_id:
            price_data['price_type'] = 'paper_option'
            price_data['paper_option_id'] = cp.paper_option_id
            price_data['paper_option_name'] = cp.paper_option.name if cp.paper_option else None
        elif cp.finishing_option_id:
            price_data['price_type'] = 'finishing_option'
            price_data['finishing_option_id'] = cp.finishing_option_id
            price_data['finishing_option_name'] = cp.finishing_option.name if cp.finishing_option else None
        elif cp.print_pricing_id:
            price_data['price_type'] = 'print_pricing'
            price_data['print_pricing_id'] = cp.print_pricing_id
            price_data['print_pricing_name'] = cp.print_pricing.name if cp.print_pricing else None
        else:
            price_data['price_type'] = 'custom'
        
        result.append(price_data)
    
    return jsonify(result)

# Helper function to get customer-specific pricing if available
def get_customer_price(customer_id, price_type, reference_id):
    """
    Get customer-specific price if available
    
    Args:
        customer_id: ID of the customer
        price_type: Type of price ('saved_price', 'paper_option', etc.)
        reference_id: ID of the referenced price
        
    Returns:
        The customer-specific price or None if not found
    """
    if not customer_id or not reference_id:
        return None
        
    # Create filter based on price type
    filters = {
        'customer_id': customer_id,
        'is_active': True
    }
    
    if price_type == 'saved_price':
        filters['saved_price_id'] = reference_id
    elif price_type == 'paper_option':
        filters['paper_option_id'] = reference_id
    elif price_type == 'finishing_option':
        filters['finishing_option_id'] = reference_id
    elif price_type == 'print_pricing':
        filters['print_pricing_id'] = reference_id
    else:
        return None
        
    # Find active customer price that matches criteria and is currently valid
    customer_price = CustomerPrice.query.filter_by(**filters).first()
    
    # Check if price is valid
    if customer_price and customer_price.is_valid:
        return customer_price.effective_price
        
    return None