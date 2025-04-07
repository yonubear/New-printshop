"""
Add Default Materials

This script adds default materials and paper types to the saved_price table,
enabling the material selector dropdown in the saved price form to work properly.

Usage:
    python add_default_materials.py
"""

import os
from app import app, db
from models import SavedPrice, PaperOption

def create_default_materials():
    """Create default materials and paper types in the saved_price table"""
    print("Creating default materials and paper types...")
    
    # Check if we already have materials
    existing_count = SavedPrice.query.filter(
        (SavedPrice.category == 'material') | 
        (SavedPrice.category == 'paper')
    ).count()
    
    if existing_count > 0:
        print(f"Found {existing_count} existing materials/papers. Skipping creation.")
        return
    
    # Add default materials
    default_materials = [
        # Basic materials
        {'name': 'Black Ink', 'description': 'Standard black ink for printing', 'category': 'material', 
         'cost_price': 0.05, 'price': 0.10, 'unit': 'each'},
        {'name': 'Color Ink', 'description': 'CMYK color ink for printing', 'category': 'material',
         'cost_price': 0.15, 'price': 0.30, 'unit': 'each'},
        {'name': 'Lamination Film - Glossy', 'description': 'Glossy lamination film', 'category': 'material',
         'cost_price': 0.50, 'price': 1.25, 'unit': 'sqft'},
        {'name': 'Lamination Film - Matte', 'description': 'Matte lamination film', 'category': 'material',
         'cost_price': 0.55, 'price': 1.35, 'unit': 'sqft'},
        {'name': 'Spiral Binding - Black', 'description': 'Black spiral binding', 'category': 'material',
         'cost_price': 0.75, 'price': 2.00, 'unit': 'each'},
        {'name': 'Staples', 'description': 'Standard staples for binding', 'category': 'material',
         'cost_price': 0.01, 'price': 0.05, 'unit': 'each'},
    ]
    
    # Create paper options based on existing paper_option entries
    print("Checking for existing paper options...")
    paper_options = PaperOption.query.all()
    
    if paper_options:
        print(f"Found {len(paper_options)} paper options, converting to saved prices...")
        for paper in paper_options:
            # Create a proper name for the paper based on available attributes
            paper_attrs = []
            if hasattr(paper, 'weight') and paper.weight:
                paper_attrs.append(paper.weight)
            if hasattr(paper, 'category') and paper.category:
                paper_attrs.append(paper.category)
            if hasattr(paper, 'color') and paper.color:
                paper_attrs.append(paper.color)
            
            paper_name = f"{' '.join(paper_attrs)} ({paper.size})" if paper_attrs else f"{paper.name} ({paper.size})"
            paper_name = paper_name.replace("  ", " ").strip()
            
            # Set default cost if not present
            cost_per_sheet = 0.05  # Default cost
            if hasattr(paper, 'cost_per_sheet') and paper.cost_per_sheet is not None:
                cost_per_sheet = paper.cost_per_sheet
            
            # Description based on available attributes
            description_parts = []
            if hasattr(paper, 'size') and paper.size:
                description_parts.append(f"Size: {paper.size}")
            if hasattr(paper, 'weight') and paper.weight:
                description_parts.append(f"Weight: {paper.weight}")
            if hasattr(paper, 'category') and paper.category:
                description_parts.append(f"Type: {paper.category}")
            if hasattr(paper, 'color') and paper.color:
                description_parts.append(f"Color: {paper.color}")
                
            description = ", ".join(description_parts)
            
            # Create saved price for this paper
            paper_price = SavedPrice(
                name=paper_name,
                description=description,
                category='paper',
                cost_price=cost_per_sheet,
                price=cost_per_sheet * 2,  # Default markup
                unit='sheet',
                sku=f"PAP-{paper.id}"
            )
            db.session.add(paper_price)
            print(f"Added paper: {paper_name}")
    else:
        print("No paper options found, adding default papers...")
        # Add some default papers if none exist
        default_papers = [
            {'name': '20# Bond White (Letter)', 'description': 'Standard white copy paper, 8.5x11', 'category': 'paper',
             'cost_price': 0.02, 'price': 0.05, 'unit': 'sheet'},
            {'name': '24# Bond White (Letter)', 'description': 'Premium white copy paper, 8.5x11', 'category': 'paper',
             'cost_price': 0.03, 'price': 0.07, 'unit': 'sheet'},
            {'name': '32# Gloss Text (Letter)', 'description': 'Glossy text paper, 8.5x11', 'category': 'paper',
             'cost_price': 0.04, 'price': 0.10, 'unit': 'sheet'},
            {'name': '80# Gloss Cover (Letter)', 'description': 'Glossy cardstock, 8.5x11', 'category': 'paper',
             'cost_price': 0.08, 'price': 0.20, 'unit': 'sheet'},
            {'name': '100# Matte Cover (Letter)', 'description': 'Heavy matte cardstock, 8.5x11', 'category': 'paper',
             'cost_price': 0.10, 'price': 0.25, 'unit': 'sheet'},
        ]
        default_materials.extend(default_papers)
    
    # Add all default materials
    for material_data in default_materials:
        material = SavedPrice(**material_data)
        db.session.add(material)
        print(f"Added material: {material_data['name']}")
    
    # Commit changes
    db.session.commit()
    print("Default materials and papers created successfully!")

if __name__ == "__main__":
    with app.app_context():
        create_default_materials()