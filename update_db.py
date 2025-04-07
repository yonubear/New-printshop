from app import app, db
from models import *
from sqlalchemy import create_engine, Table, Column, Integer, Float, ForeignKey, MetaData, text

def create_saved_price_material_link_table():
    """Create the linking table between saved price templates and materials"""
    with app.app_context():
        # Check if table already exists
        inspector = db.inspect(db.engine)
        table_exists = 'saved_price_material_link' in inspector.get_table_names()
        
        if not table_exists:
            print("Creating saved_price_material_link table...")
            
            # Create the table using a direct SQL statement
            db.session.execute(text("""
                CREATE TABLE saved_price_material_link (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id INTEGER NOT NULL,
                    material_id INTEGER NOT NULL,
                    quantity FLOAT DEFAULT 1.0,
                    FOREIGN KEY(template_id) REFERENCES saved_price(id) ON DELETE CASCADE,
                    FOREIGN KEY(material_id) REFERENCES saved_price(id) ON DELETE CASCADE
                )
            """))
            
            db.session.commit()
            print("Table created successfully!")
        else:
            print("saved_price_material_link table already exists.")

def add_test_materials():
    """Add some test material items"""
    with app.app_context():
        # Check if we already have material items
        material_count = SavedPrice.query.filter_by(category='material').count()
        
        if material_count == 0:
            print("Adding test materials...")
            materials = [
                {
                    'name': 'Premium Cardstock',
                    'description': '110# Cover, White, Glossy',
                    'category': 'material',
                    'cost_price': 0.10,
                    'price': 0.25,
                    'unit': 'sheet',
                    'sku': 'MAT-CARD-110'
                },
                {
                    'name': 'Bond Paper',
                    'description': '20# Bond, White',
                    'category': 'material',
                    'cost_price': 0.02,
                    'price': 0.05,
                    'unit': 'sheet',
                    'sku': 'MAT-BOND-20'
                },
                {
                    'name': 'Black Ink',
                    'description': 'Black Toner',
                    'category': 'material',
                    'cost_price': 0.50,
                    'price': 1.00,
                    'unit': 'ml',
                    'sku': 'MAT-INK-BLK'
                },
                {
                    'name': 'Color Ink Set',
                    'description': 'CMYK Toner Set',
                    'category': 'material',
                    'cost_price': 2.00,
                    'price': 4.00,
                    'unit': 'ml',
                    'sku': 'MAT-INK-CMYK'
                },
                {
                    'name': 'Lamination Film',
                    'description': '5mil Gloss Lamination',
                    'category': 'material',
                    'cost_price': 0.75,
                    'price': 1.50,
                    'unit': 'sqft',
                    'sku': 'MAT-LAM-5GL'
                }
            ]
            
            for material_data in materials:
                material = SavedPrice(**material_data)
                db.session.add(material)
            
            db.session.commit()
            print(f"Added {len(materials)} test materials!")
        else:
            print(f"Found {material_count} existing materials, skipping test data.")

if __name__ == '__main__':
    create_saved_price_material_link_table()
    add_test_materials()
    print("Database update complete!")