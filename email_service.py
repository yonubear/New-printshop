"""
Email service for sending proofs to customers
"""
import os
import uuid
from datetime import datetime
from urllib.parse import urljoin

from flask import current_app, url_for
from flask_mail import Mail, Message

# Initialize Flask-Mail
mail = Mail()

def init_email(app):
    """Initialize email settings"""
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', 'yes', '1')
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'printshop@example.com')
    
    # Initialize Flask-Mail extension
    mail.init_app(app)

def generate_approval_token():
    """Generate a unique approval token"""
    return str(uuid.uuid4())

def send_proof_approval_email(order_file, customer, order, base_url=None):
    """
    Send a proof to a customer for approval
    
    Args:
        order_file: The OrderFile object containing the proof
        customer: The Customer object
        order: The Order object
        base_url: Base URL for approval links (optional)
    
    Returns:
        bool: Whether the email was sent successfully
    """
    # Generate a unique token for this proof if it doesn't have one
    if not order_file.approval_token:
        order_file.approval_token = generate_approval_token()
    
    # Update the sent timestamp
    order_file.proof_sent_at = datetime.utcnow()
    
    # Create approval URLs
    if not base_url:
        # Default base URL (for development)
        base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Generate approval and rejection URLs
    approve_url = urljoin(base_url, f'/proof/approve/{order_file.approval_token}')
    reject_url = urljoin(base_url, f'/proof/reject/{order_file.approval_token}')
    view_url = urljoin(base_url, f'/proof/view/{order_file.approval_token}')
    
    # Construct the email
    subject = f'Proof Approval Request - {order.order_number}'
    
    # Create the message
    msg = Message(
        subject=subject,
        recipients=[customer.email],
        html=f'''
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; font-size: 24px; margin-bottom: 20px; }}
                    h2 {{ color: #3498db; font-size: 20px; margin-bottom: 15px; }}
                    p {{ margin-bottom: 15px; }}
                    .btn {{ display: inline-block; padding: 10px 20px; margin-right: 10px; margin-bottom: 10px; 
                           text-decoration: none; border-radius: 4px; font-weight: bold; text-align: center; }}
                    .btn-primary {{ background-color: #3498db; color: white; }}
                    .btn-success {{ background-color: #2ecc71; color: white; }}
                    .btn-danger {{ background-color: #e74c3c; color: white; }}
                    .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #eee; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Proof Approval Request</h1>
                    <p>Dear {customer.name},</p>
                    <p>We've prepared a proof for your order <strong>{order.order_number}: {order.title}</strong> and would like your approval before proceeding with production.</p>
                    
                    <h2>Proof Details</h2>
                    <p><strong>File:</strong> {order_file.original_filename}</p>
                    <p><strong>Type:</strong> {order_file.file_type.capitalize()}</p>
                    <p><strong>Uploaded:</strong> {order_file.uploaded_at.strftime('%Y-%m-%d %H:%M')}</p>
                    
                    <p>Please review the proof by clicking the button below:</p>
                    <p><a href="{view_url}" class="btn btn-primary">View Proof</a></p>
                    
                    <p>After reviewing, please approve or request changes:</p>
                    <p>
                        <a href="{approve_url}" class="btn btn-success">Approve Proof</a>
                        <a href="{reject_url}" class="btn btn-danger">Request Changes</a>
                    </p>
                    
                    <p>If you have any questions or need clarification about the proof, please contact us directly.</p>
                    
                    <p>Thank you for your business!</p>
                    
                    <div class="footer">
                        <p>This email was sent automatically from our Print Shop Management System.</p>
                    </div>
                </div>
            </body>
        </html>
        '''
    )
    
    # Send the email
    try:
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send proof approval email: {str(e)}")
        return False