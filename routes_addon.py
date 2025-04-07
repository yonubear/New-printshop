# Import required modules
import io
import qrcode
from flask import request, Response, render_template
from app import app
from models import Order

# Order QR Code generation
@app.route('/order/qrcode/<int:order_id>')
def order_qr_code(order_id):
    """Generate a QR code image for tracking an order"""
    order = Order.query.get_or_404(order_id)
    
    # Ensure tracking code exists
    tracking_code = order.get_or_create_tracking_code()
    
    # Get base URL for tracking link
    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/track/{tracking_code}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return Response(img_io, mimetype='image/png')

# Order tracking page
@app.route('/track/<tracking_code>')
def track_order(tracking_code):
    """Public tracking page for orders"""
    # Find order with the given tracking code
    order = Order.query.filter_by(tracking_code=tracking_code).first_or_404()
    
    return render_template('orders/track.html', order=order)