from flask import render_template, jsonify, request
from flask_wtf import FlaskForm
from app import app, db, csrf
from models import PaperOption, PrintPricing, FinishingOption


@app.route('/print-preview', methods=['GET'])
def print_preview():
    """Interactive print preview page with real-time material cost estimation"""
    # Create a simple form for CSRF protection
    class PreviewForm(FlaskForm):
        pass
    
    form = PreviewForm()
    
    # Get all paper sizes for the dropdown
    paper_sizes = db.session.query(PaperOption.size).distinct().all()
    sizes = sorted([size[0] for size in paper_sizes if size[0]])
    
    # Get all paper weights for the dropdown
    paper_weights = db.session.query(PaperOption.weight).distinct().all()
    weights = sorted([weight[0] for weight in paper_weights if weight[0]])
    
    # Get all paper categories for the dropdown
    paper_categories = db.session.query(PaperOption.category).distinct().all()
    categories = sorted([category[0] for category in paper_categories if category[0]])
    
    # Get all color types for the dropdown
    color_types = db.session.query(PrintPricing.color_type).distinct().all()
    color_options = sorted([color[0] for color in color_types if color[0]])
    
    # Get all finishing options categories
    finishing_categories = db.session.query(FinishingOption.category).distinct().all()
    finishing_categories = sorted([cat[0] for cat in finishing_categories if cat[0]])
    
    return render_template(
        'print_preview/index.html',
        form=form,
        paper_sizes=sizes,
        paper_weights=weights,
        paper_categories=categories,
        color_options=color_options,
        finishing_categories=finishing_categories
    )


@app.route('/api/preview/cost-estimate', methods=['POST'])
def api_preview_cost_estimate():
    """API endpoint to get real-time cost estimation for a print job"""
    data = request.json
    
    # Extract parameters
    paper_id = data.get('paper_id')
    color_type = data.get('color_type') 
    sides = data.get('sides', 'Single-sided')
    quantity = int(data.get('quantity', 1))
    finishing_ids = data.get('finishing_ids', [])
    
    # Validate parameters
    if not paper_id or not color_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Get paper info
        paper = PaperOption.query.get(paper_id)
        if not paper:
            return jsonify({'error': 'Paper option not found'}), 404
            
        # Get print pricing
        pricing = PrintPricing.query.filter_by(
            paper_size=paper.size, 
            color_type=color_type
        ).first()
        
        if not pricing:
            # Try to find a generic pricing
            pricing = PrintPricing.query.filter_by(
                color_type=color_type
            ).filter(PrintPricing.paper_size.in_(['Any', 'Universal'])).first()
            
        if not pricing:
            return jsonify({'error': 'Print pricing not found for this combination'}), 404
            
        # Calculate base price
        num_sides = 2 if sides == 'Double-sided' else 1
        paper_cost = paper.price_per_sheet
        paper_cost_price = paper.cost_per_sheet
        printing_cost = pricing.price_per_side * num_sides
        printing_cost_price = pricing.cost_per_side * num_sides
        
        unit_price = paper_cost + printing_cost
        unit_cost = paper_cost_price + printing_cost_price
        
        # Add finishing options pricing
        finishing_cost = 0
        finishing_cost_breakdown = []
        
        if finishing_ids:
            for finishing_id in finishing_ids:
                option = FinishingOption.query.get(finishing_id)
                if option:
                    # Calculate effective cost based on quantity
                    option_price = option.base_price
                    if option.price_per_piece > 0:
                        option_price += option.price_per_piece * quantity
                        
                    # Apply minimum price if set
                    if option.minimum_price > 0:
                        option_price = max(option_price, option.minimum_price)
                        
                    finishing_cost += option_price
                    finishing_cost_breakdown.append({
                        'name': option.name,
                        'price': option_price
                    })
        
        # Calculate final prices
        total_unit_price = unit_price + (finishing_cost / max(1, quantity))
        total_price = (unit_price * quantity) + finishing_cost
        total_cost = unit_cost * quantity  # Cost price doesn't include finishing option costs
        estimated_profit = total_price - total_cost
        profit_margin = (estimated_profit / total_price) * 100 if total_price > 0 else 0
        
        # Format result
        result = {
            'paper': {
                'name': paper.name,
                'category': paper.category,
                'size': paper.size,
                'weight': paper.weight,
                'price_per_sheet': paper.price_per_sheet,
                'cost_per_sheet': paper.cost_per_sheet
            },
            'printing': {
                'price_per_side': pricing.price_per_side,
                'cost_per_side': pricing.cost_per_side,
                'color_type': pricing.color_type,
                'sides': sides,
                'num_sides': num_sides
            },
            'finishing': {
                'total_cost': finishing_cost,
                'breakdown': finishing_cost_breakdown
            },
            'prices': {
                'unit_price': round(unit_price, 2),
                'total_price': round(total_price, 2),
                'unit_with_finishing': round(total_unit_price, 2)
            },
            'costs': {
                'unit_cost': round(unit_cost, 2),
                'total_cost': round(total_cost, 2),
                'estimated_profit': round(estimated_profit, 2),
                'profit_margin': round(profit_margin, 2)
            },
            'quantity': quantity
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500