import pandas as pd

def create_sample_excel():
    """Create a sample Excel template for pricing import"""
    
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
    
    # Save to Excel
    df.to_excel('pricing_template.xlsx', index=False)
    print("Sample Excel template created: pricing_template.xlsx")

if __name__ == "__main__":
    create_sample_excel()