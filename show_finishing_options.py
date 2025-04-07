from main import app
from models import FinishingOption

with app.app_context():
    # Get all finishing options
    finishing_options = FinishingOption.query.all()
    
    # Extract unique categories
    categories = set()
    
    print("Finishing Options:")
    for option in finishing_options:
        print(f"ID: {option.id}, Name: {option.name}, Category: {option.category}")
        if option.category:
            categories.add(option.category)
    
    print("\nUnique Categories:")
    for category in sorted(categories):
        print(f"- {category}")
        
    print("\nOptions by Category:")
    for category in sorted(categories):
        print(f"\n{category}:")
        options = FinishingOption.query.filter_by(category=category).order_by(FinishingOption.name).all()
        for option in options:
            print(f"  - {option.name} (Base: ${option.base_price}, Per piece: ${option.price_per_piece})")