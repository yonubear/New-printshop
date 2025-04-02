import os
import tempfile
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.pagesizes import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import qrcode
from PIL import Image as PILImage
from models import SavedPrice

def generate_qr_code(data):
    """Generate a QR code image for the given data and return as a ReportLab Image"""
    if not data or data == 'N/A':
        return None
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create PIL image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to reportlab Image
    img_bytes = io.BytesIO()
    qr_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return Image(img_bytes, width=0.8*inch, height=0.8*inch)

def generate_order_form(order):
    """Generate a PDF order form for the given order"""
    
    # Create a temporary file for the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.close()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,
    ))
    
    # Create the content
    content = []
    
    # Add title
    content.append(Paragraph("ORDER FORM", styles['Center']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add order information
    content.append(Paragraph(f"Order #: {order.order_number}", styles['Heading2']))
    content.append(Paragraph(f"Date: {order.created_at.strftime('%Y-%m-%d')}", styles['Normal']))
    content.append(Paragraph(f"Due Date: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'N/A'}", styles['Normal']))
    content.append(Paragraph(f"Status: {order.status.upper()}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add customer information
    content.append(Paragraph("Customer Information", styles['Heading3']))
    content.append(Paragraph(f"Name: {order.customer.name}", styles['Normal']))
    content.append(Paragraph(f"Email: {order.customer.email}", styles['Normal']))
    content.append(Paragraph(f"Phone: {order.customer.phone or 'N/A'}", styles['Normal']))
    content.append(Paragraph(f"Company: {order.customer.company or 'N/A'}", styles['Normal']))
    
    if order.customer.address:
        content.append(Paragraph(f"Address: {order.customer.address}", styles['Normal']))
        
    content.append(Spacer(1, 0.25 * inch))
    
    # Add order description
    content.append(Paragraph("Order Description", styles['Heading3']))
    content.append(Paragraph(f"Title: {order.title}", styles['Normal']))
    
    if order.description:
        content.append(Paragraph(f"Description: {order.description}", styles['Normal']))
        
    content.append(Spacer(1, 0.25 * inch))
    
    # Add order items
    content.append(Paragraph("Order Items", styles['Heading3']))
    
    if order.items:
        # Create table for order items
        item_data = [['Item', 'SKU', 'Description', 'Quantity', 'Unit Price', 'Total']]
        
        # Add items to table
        for item in order.items:
            item_data.append([
                item.name,
                item.sku or 'N/A',
                item.description or 'N/A',
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.total_price:.2f}"
            ])
            
        # Add total row
        item_data.append(['', '', '', '', 'Total:', f"${order.total_price:.2f}"])
        
        # Create table
        item_table = Table(item_data, colWidths=[1.0*inch, 0.8*inch, 1.5*inch, 0.6*inch, 0.8*inch, 0.8*inch])
        
        # Apply table style
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (1, 1), (1, -2), 'CENTER'),  # Center SKU column
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),  # Center quantity column
            ('ALIGN', (4, 1), (5, -1), 'RIGHT'),  # Right align price columns
            ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        content.append(item_table)
    else:
        content.append(Paragraph("No items in this order", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add notes and signing
    content.append(Paragraph("Notes:", styles['Heading4']))
    content.append(Spacer(1, 0.5 * inch))
    
    # Add signature lines
    sig_data = [
        ['', ''],
        ['________________________', '________________________'],
        ['Customer Signature', 'Date'],
        ['', ''],
        ['________________________', '________________________'],
        ['Authorized Signature', 'Date'],
    ]
    
    sig_table = Table(sig_data, colWidths=[2.5*inch, 2.5*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    content.append(sig_table)
    
    # Build the PDF document
    doc.build(content)
    
    return temp_file.name

def generate_pull_sheet(order):
    """Generate a PDF material pull sheet for the given order on a 4"x6" page size with QR codes"""
    
    # Create a temporary file for the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.close()
    
    # Define a custom page size (4" x 6")
    four_by_six = (4*inch, 6*inch)
    
    # Create the PDF document with 4x6 page size
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=four_by_six,
        rightMargin=0.2*inch,
        leftMargin=0.2*inch,
        topMargin=0.2*inch,
        bottomMargin=0.2*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,
        fontSize=14,
    ))
    
    # Update styles to fit smaller page size
    styles.add(ParagraphStyle(
        name='SmallHeading',
        parent=styles['Heading2'],
        fontSize=12,
    ))
    
    styles.add(ParagraphStyle(
        name='SmallNormal',
        parent=styles['Normal'],
        fontSize=7,
    ))
    
    styles.add(ParagraphStyle(
        name='SmallHeading3',
        parent=styles['Heading3'],
        fontSize=10,
    ))
    
    # Create the content
    content = []
    
    # Add title
    content.append(Paragraph("MATERIAL PULL SHEET", styles['Center']))
    content.append(Spacer(1, 0.1 * inch))
    
    # Add order information
    content.append(Paragraph(f"Order #: {order.order_number}", styles['SmallHeading']))
    content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['SmallNormal']))
    content.append(Paragraph(f"Due: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'N/A'}", styles['SmallNormal']))
    
    # Add customer and order information
    content.append(Paragraph(f"Customer: {order.customer.name}", styles['SmallHeading3']))
    content.append(Paragraph(f"Order: {order.title}", styles['SmallNormal']))
    content.append(Spacer(1, 0.1 * inch))
    
    # Process materials
    all_materials = []
    for item in order.items:
        for material in item.materials:
            all_materials.append((item.name, material))
    
    if all_materials:
        # Create multiple material cards per page (3 cards per page)
        items_per_page = 3
        
        # Process materials in batches
        for i in range(0, len(all_materials), items_per_page):
            # Get current batch of materials (up to items_per_page)
            batch = all_materials[i:i+items_per_page]
            
            # Add page break for new pages after the first page
            if i > 0:
                content.append(PageBreak())
                # Add the header again for each new page
                content.append(Paragraph("MATERIAL PULL SHEET", styles['Center']))
                content.append(Spacer(1, 0.1 * inch))
                content.append(Paragraph(f"Order #: {order.order_number}", styles['SmallHeading']))
                content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['SmallNormal']))
                content.append(Paragraph(f"Due: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'N/A'}", styles['SmallNormal']))
                content.append(Paragraph(f"Customer: {order.customer.name}", styles['SmallHeading3']))
                content.append(Paragraph(f"Order: {order.title}", styles['SmallNormal']))
                content.append(Spacer(1, 0.1 * inch))
            
            # Process each material in the batch
            for idx, (item_name, material) in enumerate(batch):
                # Add smaller spacer between items on the same page
                if idx > 0:
                    content.append(Spacer(1, 0.1 * inch))
                
                # Create a container for material info
                material_data = []
                
                # Find the SKU - from the material's saved_price if available, otherwise from the item
                item_sku = next((item.sku for item in order.items if item.name == item_name), 'N/A')
                material_sku = 'N/A'
                
                # Safely access the saved_price relationship
                if hasattr(material, 'saved_price_id') and material.saved_price_id:
                    saved_price = SavedPrice.query.get(material.saved_price_id)
                    if saved_price and saved_price.sku:
                        material_sku = saved_price.sku
                
                # If no saved_price SKU was found, use the item SKU as a fallback
                if material_sku == 'N/A':
                    material_sku = item_sku
                
                # Generate QR code for the SKU if available
                qr_code = None
                if material_sku and material_sku != 'N/A':
                    qr_code = generate_qr_code(material_sku)
                
                # Use smaller size for QR code for 3-up layout
                qr_code_size = 0.6*inch
                if qr_code:
                    qr_code._width = qr_code_size
                    qr_code._height = qr_code_size
                
                # Create more compact header row with QR code and material info
                header_data = [[
                    Paragraph(f"<b>Material:</b> {material.material_name}", styles['SmallHeading3']),
                    qr_code if qr_code else Paragraph("", styles['SmallNormal'])
                ]]
                
                header_table = Table(header_data, colWidths=[2.4*inch, 1.0*inch])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ]))
                
                material_data.append([header_table])
                
                # Create more compact details format
                details_data = [
                    [Paragraph(f"<b>Item:</b> {item_name}", styles['SmallNormal'])],
                    [Paragraph(f"<b>SKU:</b> {material_sku}", styles['SmallNormal'])],
                    [Paragraph(f"<b>Qty:</b> {material.quantity} {material.unit}", styles['SmallNormal'])],
                ]
                
                if material.notes:
                    # Truncate notes if too long
                    notes = material.notes
                    if len(notes) > 50:
                        notes = notes[:47] + "..."
                    details_data.append([Paragraph(f"<b>Notes:</b> {notes}", styles['SmallNormal'])])
                
                details_table = Table(details_data)
                details_table.setStyle(TableStyle([
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ]))
                
                material_data.append([details_table])
                
                # Add compact checkbox for marking as pulled
                checkbox_data = [[
                    Paragraph("Pulled:", styles['SmallNormal']),
                    "□ _________"
                ]]
                
                checkbox_table = Table(checkbox_data, colWidths=[0.8*inch, 2.6*inch])
                checkbox_table.setStyle(TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                material_data.append([checkbox_table])
                
                # Create main table to hold all the components with smaller margins
                main_table = Table(material_data, colWidths=[3.4*inch])
                main_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                content.append(main_table)
    else:
        content.append(Paragraph("No materials specified for this order", styles['SmallNormal']))
    
    # Build the PDF document
    doc.build(content)
    
    return temp_file.name

def generate_quote_pdf(quote):
    """Generate a PDF quote for the given quote"""
    
    # Create a temporary file for the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.close()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Heading1'],
        alignment=1,
    ))
    
    # Create the content
    content = []
    
    # Add title
    content.append(Paragraph("QUOTE", styles['Center']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add quote information
    content.append(Paragraph(f"Quote #: {quote.quote_number}", styles['Heading2']))
    content.append(Paragraph(f"Date: {quote.created_at.strftime('%Y-%m-%d')}", styles['Normal']))
    
    if quote.valid_until:
        content.append(Paragraph(f"Valid Until: {quote.valid_until.strftime('%Y-%m-%d')}", styles['Normal']))
    
    content.append(Paragraph(f"Status: {quote.status.upper()}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add customer information
    content.append(Paragraph("Customer Information", styles['Heading3']))
    content.append(Paragraph(f"Name: {quote.customer.name}", styles['Normal']))
    content.append(Paragraph(f"Email: {quote.customer.email}", styles['Normal']))
    content.append(Paragraph(f"Phone: {quote.customer.phone or 'N/A'}", styles['Normal']))
    content.append(Paragraph(f"Company: {quote.customer.company or 'N/A'}", styles['Normal']))
    
    if quote.customer.address:
        content.append(Paragraph(f"Address: {quote.customer.address}", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add quote description
    content.append(Paragraph("Quote Description", styles['Heading3']))
    content.append(Paragraph(f"Title: {quote.title}", styles['Normal']))
    
    if quote.description:
        content.append(Paragraph(f"Description: {quote.description}", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add quote items
    content.append(Paragraph("Quote Items", styles['Heading3']))
    
    if quote.items:
        # Create table for quote items
        item_data = [['Item', 'Specifications', 'Quantity', 'Unit Price', 'Total']]
        
        # Add items to table
        for item in quote.items:
            # Build specifications text
            specs = []
            if item.size == 'Custom' and item.custom_width and item.custom_height:
                specs.append(f"Size: {item.custom_width}\" x {item.custom_height}\"")
            elif item.size:
                specs.append(f"Size: {item.size}")
                
            if item.color_type:
                specs.append(f"Color: {item.color_type}")
                
            if item.sides:
                specs.append(f"{item.sides}")
                
            if item.paper_type or item.paper_weight:
                paper_spec = "Paper: "
                if item.paper_type:
                    paper_spec += item.paper_type
                if item.paper_weight:
                    paper_spec += f" {item.paper_weight}"
                specs.append(paper_spec)
                
            if item.finishing_options:
                specs.append(f"Finishing: {item.finishing_options.replace(',', ', ')}")
                
            specifications = "\n".join(specs)
            
            item_data.append([
                item.name,
                specifications,
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.total_price:.2f}"
            ])
            
        # Add total row
        item_data.append(['', '', '', 'Subtotal:', f"${quote.total_price:.2f}"])
        item_data.append(['', '', '', 'Total:', f"${quote.total_price:.2f}"])
        
        # Create table
        item_table = Table(item_data, colWidths=[1.2*inch, 2.3*inch, 0.6*inch, 0.8*inch, 0.8*inch])
        
        # Apply table style
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (2, 1), (2, -3), 'CENTER'),  # Center quantity column
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),  # Right align price columns
            ('GRID', (0, 0), (-1, -3), 1, colors.black),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        content.append(item_table)
    else:
        content.append(Paragraph("No items in this quote", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add terms and conditions
    content.append(Paragraph("Terms and Conditions", styles['Heading3']))
    
    terms = [
        "All quoted prices are valid for 30 days from the date of this quote unless otherwise specified.",
        "This quote does not include rush fees, delivery fees, or applicable taxes unless explicitly stated in the quote items.",
        "Payment terms: 50% deposit required to begin work, with the remaining balance due upon completion of the job before delivery.",
        "Turnaround time begins after proof approval and payment of deposit.",
        "Customer-supplied files must be print-ready. Additional charges may apply for file corrections or adjustments."
    ]
    
    for term in terms:
        content.append(Paragraph(f"• {term}", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add signature lines
    sig_data = [
        ['', ''],
        ['________________________', '________________________'],
        ['Customer Signature', 'Date'],
        ['', ''],
        ['________________________', '________________________'],
        ['Print Shop Authorization', 'Date'],
    ]
    
    sig_table = Table(sig_data, colWidths=[2.5*inch, 2.5*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    content.append(sig_table)
    
    # Build the PDF document
    doc.build(content)
    
    return temp_file.name
