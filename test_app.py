import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Create a base class for declarative models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = "test-secret-key"

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db.init_app(app)

# Define models
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
    
    materials = db.relationship('SavedPriceMaterial', backref='saved_price', lazy=True, cascade="all, delete-orphan")

class SavedPriceMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    saved_price_id = db.Column(db.Integer, db.ForeignKey('saved_price.id'), nullable=False)
    material_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), default='pcs')  # pcs, sheets, sq_ft, etc.
    cost_price = db.Column(db.Float, default=0.0)  # Optional cost price for this material
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))  # material category: 'paper', 'ink', 'substrate', etc.

# Routes
@app.route('/')
def index():
    return redirect(url_for('saved_prices_index'))

@app.route('/saved_prices')
def saved_prices_index():
    categories = SavedPrice.query.with_entities(SavedPrice.category).distinct().all()
    categories = [c[0] for c in categories]  # Extract values from Row objects
    
    # Query with filtering
    category_filter = request.args.get('category')
    query = SavedPrice.query
    
    if category_filter:
        query = query.filter_by(category=category_filter)
    
    # Get all saved prices, sorted by name
    saved_prices = query.order_by(SavedPrice.name).all()
    
    return render_template('saved_prices/index.html', 
                          saved_prices=saved_prices, 
                          categories=categories,
                          selected_category=category_filter or 'all')

@app.route('/saved_prices/create', methods=['GET', 'POST'])
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
            # For template material approach with JavaScript
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            
            print(f"Template material IDs: {template_material_ids}")
            print(f"Template material quantities: {template_material_quantities}")
            
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
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) else 1
                
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

@app.route('/saved_prices/<int:id>/edit', methods=['GET', 'POST'])
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
            # Remove all existing materials
            SavedPriceMaterial.query.filter_by(saved_price_id=id).delete()
            
            # Add new materials from form
            template_material_ids = request.form.getlist('template_material_ids[]')
            template_material_quantities = request.form.getlist('template_material_quantities[]')
            
            print(f"Updating material IDs: {template_material_ids}")
            print(f"Updating material quantities: {template_material_quantities}")
            
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
                quantity = float(template_material_quantities[i]) if i < len(template_material_quantities) else 1
                
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

# Initialize database with sample data
def initialize_db():
    # Create sample materials if they don't exist
    if SavedPrice.query.filter_by(category='material').count() == 0:
        materials = [
            {
                'name': '24pt Card Stock',
                'category': 'paper',
                'price': 0.75,
                'cost_price': 0.3,
                'unit': 'sheet',
                'description': 'Heavy card stock for business cards'
            },
            {
                'name': '16pt Matte Paper',
                'category': 'paper',
                'price': 0.50,
                'cost_price': 0.2,
                'unit': 'sheet',
                'description': 'Standard matte finish paper'
            },
            {
                'name': 'Laminate Gloss',
                'category': 'material',
                'price': 1.2,
                'cost_price': 0.4,
                'unit': 'sqft',
                'description': 'Glossy laminate finish'
            }
        ]
        
        for material in materials:
            new_material = SavedPrice(
                name=material['name'],
                category=material['category'],
                price=material['price'],
                cost_price=material['cost_price'],
                unit=material['unit'],
                description=material['description'],
                is_template=False
            )
            db.session.add(new_material)
        
        db.session.commit()

# Create app context and initialize
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_db()
    
    app.run(host='0.0.0.0', port=5001, debug=True)