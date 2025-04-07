from main import app
from models import FinishingOption, db

# Define finishing options by category
finishing_options = {
    "Binding": [
        {"name": "Comb Binding", "description": "Plastic comb binding", "base_price": 3.50, "price_per_piece": 0.10, "minimum_price": 3.50},
        {"name": "Spiral Binding", "description": "Coil binding", "base_price": 4.00, "price_per_piece": 0.15, "minimum_price": 4.00},
        {"name": "Wire-O Binding", "description": "Wire binding", "base_price": 5.00, "price_per_piece": 0.20, "minimum_price": 5.00},
        {"name": "Perfect Binding", "description": "Glue binding", "base_price": 8.00, "price_per_piece": 0.30, "minimum_price": 8.00},
    ],
    "Folding": [
        {"name": "Half Fold", "description": "Single fold in middle", "base_price": 0.05, "price_per_piece": 0.05, "minimum_price": 5.00},
        {"name": "Tri-Fold", "description": "Letter fold into thirds", "base_price": 0.08, "price_per_piece": 0.08, "minimum_price": 8.00},
        {"name": "Z-Fold", "description": "Accordion fold", "base_price": 0.10, "price_per_piece": 0.10, "minimum_price": 10.00},
        {"name": "Gate Fold", "description": "Panels fold to center", "base_price": 0.15, "price_per_piece": 0.15, "minimum_price": 15.00},
        {"name": "Double Parallel Fold", "description": "Four panel fold", "base_price": 0.12, "price_per_piece": 0.12, "minimum_price": 12.00},
    ],
    "Stapling": [
        {"name": "Corner Staple", "description": "Single staple in corner", "base_price": 0.02, "price_per_piece": 0.02, "minimum_price": 2.00},
        {"name": "Saddle Stitch", "description": "Staples along fold", "base_price": 0.05, "price_per_piece": 0.03, "minimum_price": 3.00},
    ],
    "Lamination": [
        {"name": "Pouch Lamination", "description": "Individual sheet lamination", "base_price": 1.00, "price_per_piece": 1.00, "minimum_price": 1.00},
        {"name": "Roll Lamination", "description": "Continuous roll lamination", "base_price": 1.50, "price_per_sqft": 0.50, "minimum_price": 1.50},
    ],
    "Cutting": [
        {"name": "Standard Cut", "description": "Straight cuts on sheets", "base_price": 2.00, "price_per_piece": 0.01, "minimum_price": 2.00},
        {"name": "Die Cutting", "description": "Custom shape cutting", "base_price": 50.00, "price_per_piece": 0.10, "minimum_price": 50.00},
        {"name": "Corner Rounding", "description": "Rounded corners", "base_price": 5.00, "price_per_piece": 0.05, "minimum_price": 5.00},
    ],
    "Finishing": [
        {"name": "Scoring", "description": "Creasing for clean folds", "base_price": 5.00, "price_per_piece": 0.05, "minimum_price": 5.00},
        {"name": "Perforating", "description": "Line of small holes for tearing", "base_price": 8.00, "price_per_piece": 0.05, "minimum_price": 8.00},
        {"name": "Drilling", "description": "Hole punching for binders", "base_price": 3.00, "price_per_piece": 0.02, "minimum_price": 3.00},
        {"name": "Numbering", "description": "Sequential numbering", "base_price": 10.00, "price_per_piece": 0.10, "minimum_price": 10.00},
    ],
    "Coating": [
        {"name": "Gloss Coating", "description": "Shiny UV coating", "base_price": 15.00, "price_per_sqft": 0.20, "minimum_price": 15.00},
        {"name": "Matte Coating", "description": "Non-reflective coating", "base_price": 15.00, "price_per_sqft": 0.20, "minimum_price": 15.00},
        {"name": "Spot UV", "description": "Selective gloss coating", "base_price": 50.00, "price_per_sqft": 0.30, "minimum_price": 50.00},
    ],
}

with app.app_context():
    # Check existing options to avoid duplicates
    existing_options = {option.name: option for option in FinishingOption.query.all()}
    
    # Add options
    added_count = 0
    
    for category, options in finishing_options.items():
        for option_data in options:
            name = option_data["name"]
            
            # Skip if option already exists
            if name in existing_options:
                print(f"Option '{name}' already exists, updating category to '{category}'")
                existing_option = existing_options[name]
                existing_option.category = category
                db.session.add(existing_option)
                continue
                
            # Create new option
            option = FinishingOption(
                name=name,
                description=option_data["description"],
                category=category,
                base_price=option_data["base_price"],
                price_per_piece=option_data.get("price_per_piece", 0),
                price_per_sqft=option_data.get("price_per_sqft", 0),
                minimum_price=option_data.get("minimum_price", 0)
            )
            db.session.add(option)
            print(f"Added '{name}' to category '{category}'")
            added_count += 1
    
    db.session.commit()
    print(f"\nAdded {added_count} new finishing options across {len(finishing_options)} categories.")