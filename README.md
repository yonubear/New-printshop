# Print Shop Management System

A comprehensive print order management system designed to streamline print job workflows with robust quoting and order tracking capabilities. Provides advanced features for detailed quote creation, price management, and customizable order processing, with a focus on dynamic material handling and flexible pricing templates.

## Features

- **Order Management**: Create and track print orders from quote to completion
- **Customer Management**: Store and manage customer information
- **File Management**: Upload, store, and preview files with Nextcloud integration
- **Quoting System**: Create detailed quotes with custom specifications
- **Material Management**: Track materials used in print jobs
- **Saved Prices**: Store and reuse pricing for common print jobs
- **PDF Generation**: Generate order forms, pull sheets, and quotes as PDFs
- **Customer Proof Approval**: Send proofs to customers via email for approval
- **Barcode Scanning**: Scan order/quote numbers via smartphone camera

## Key Technologies

- Flask backend
- SQLAlchemy for database management
- Jinja2 templating
- Bootstrap 5 for responsive design
- Nextcloud integration
- PDF generation capabilities
- jQuery for client-side interactions
- Excel template generation support
- Email integration for customer proofs

## Exporting the Project

To export this project for use on your own Nextcloud environment:

1. **Create a ZIP archive** of all project files
   ```bash
   zip -r printshop_management.zip . -x "*.git*" "venv/*" "instance/*" "__pycache__/*" "*.pyc"
   ```

2. **Transfer the ZIP file** to your server or download it to your local machine

3. **Extract the archive** on your target environment
   ```bash
   unzip printshop_management.zip -d /path/to/destination
   ```

4. **Follow the setup instructions** in the `SETUP_GUIDE.md` file to configure and run the application

## Configuration

Before running the application, you'll need to:

1. Set up a Nextcloud account and configure credentials
2. Configure email settings for sending customer proofs
3. Create an admin user

See the `SETUP_GUIDE.md` file for detailed configuration instructions.

## Default Admin Credentials

- Username: `admin`
- Password: `password123`

**Important**: Change these credentials immediately after first login.