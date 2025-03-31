import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

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
    """Generate a PDF material pull sheet for the given order"""
    
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
    content.append(Paragraph("MATERIAL PULL SHEET", styles['Center']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add order information
    content.append(Paragraph(f"Order #: {order.order_number}", styles['Heading2']))
    content.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    content.append(Paragraph(f"Due Date: {order.due_date.strftime('%Y-%m-%d') if order.due_date else 'N/A'}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add customer and order information
    content.append(Paragraph(f"Customer: {order.customer.name}", styles['Heading3']))
    content.append(Paragraph(f"Order Title: {order.title}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Add materials section
    content.append(Paragraph("Required Materials", styles['Heading3']))
    
    all_materials = []
    for item in order.items:
        for material in item.materials:
            all_materials.append((item.name, material))
    
    if all_materials:
        # Create table for materials
        material_data = [['Order Item', 'SKU', 'Material', 'Quantity', 'Unit', 'Notes', 'Pulled']]
        
        # Add materials to table
        for item_name, material in all_materials:
            # Find the SKU for this item
            item_sku = next((item.sku for item in order.items if item.name == item_name), 'N/A')
            
            material_data.append([
                item_name,
                item_sku or 'N/A',  # Show SKU or N/A if not available
                material.material_name,
                str(material.quantity),
                material.unit,
                material.notes or '',
                '□'  # Checkbox for marking pulled items
            ])
            
        # Create table
        material_table = Table(material_data, colWidths=[1.1*inch, 0.8*inch, 1.1*inch, 0.6*inch, 0.5*inch, 1.4*inch, 0.5*inch])
        
        # Apply table style
        material_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Center SKU column
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Center quantity and unit columns
            ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),  # Center pulled checkbox
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        content.append(material_table)
    else:
        content.append(Paragraph("No materials specified for this order", styles['Normal']))
    
    content.append(Spacer(1, 0.25 * inch))
    
    # Add notes and sign-off
    content.append(Paragraph("Notes:", styles['Heading4']))
    content.append(Spacer(1, 0.5 * inch))
    
    # Add signature lines
    sig_data = [
        ['________________________', '________________________'],
        ['Pulled By', 'Date'],
        ['', ''],
        ['________________________', '________________________'],
        ['Verified By', 'Date'],
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
