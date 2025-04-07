# Print Shop Management System - Apache Deployment Guide

This guide will help you deploy the Print Shop Management System on an Apache web server.

## Prerequisites

- A server with Apache installed
- Python 3.9+ installed
- PostgreSQL database server
- Git (optional, for cloning the repository)

## Step 1: Install Required Packages

First, install Apache, mod_wsgi, and other required system packages:

```bash
# For Debian/Ubuntu systems
sudo apt-get update
sudo apt-get install apache2 apache2-dev libapache2-mod-wsgi-py3 python3-pip python3-dev

# For CentOS/RHEL systems
sudo yum install httpd httpd-devel python3-pip python3-devel
sudo yum install mod_wsgi
```

## Step 2: Set Up Python Virtual Environment (Optional but Recommended)

```bash
# Navigate to the directory where you want to install the application
cd /var/www

# Clone or copy the repository
# Option 1: Clone from Git (if available)
# git clone [repository-url] printshop

# Option 2: Copy the files from your local system
# scp -r /path/to/local/printshop user@server:/var/www/printshop

# Create and activate a virtual environment
python3 -m pip install virtualenv
python3 -m virtualenv printshop_env
source printshop_env/bin/activate

# Install dependencies
cd printshop
pip install -r dependencies.txt
pip install mod_wsgi
```

## Step 3: Configure PostgreSQL Database

```bash
# Create a database
sudo -u postgres psql -c "CREATE DATABASE printshop;"
sudo -u postgres psql -c "CREATE USER printshop_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE printshop TO printshop_user;"

# Edit your .env file to include database connection details
echo "DATABASE_URL=postgresql://printshop_user:your_secure_password@localhost/printshop" >> .env
```

## Step 4: Create WSGI File

Create a `wsgi.py` file in the root directory of your project:

```python
import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import the Flask application
from main import app as application

# If you're using the Flask development server
if __name__ == "__main__":
    application.run()
```

## Step 5: Configure Apache

Create a new Apache configuration file for your application:

```bash
sudo nano /etc/apache2/sites-available/printshop.conf
```

Add the following configuration (adjust paths and domain as needed):

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAdmin webmaster@yourdomain.com
    
    # Set the document root
    DocumentRoot /var/www/printshop
    
    # WSGI configuration
    WSGIDaemonProcess printshop python-home=/var/www/printshop_env python-path=/var/www/printshop
    WSGIProcessGroup printshop
    WSGIScriptAlias / /var/www/printshop/wsgi.py
    
    # Directory permissions
    <Directory /var/www/printshop>
        Require all granted
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    
    # Static files directory
    Alias /static /var/www/printshop/static
    <Directory /var/www/printshop/static>
        Require all granted
    </Directory>
    
    # Log files
    ErrorLog ${APACHE_LOG_DIR}/printshop-error.log
    CustomLog ${APACHE_LOG_DIR}/printshop-access.log combined
</VirtualHost>
```

## Step 6: Set Permissions

Ensure Apache can access the files:

```bash
sudo chown -R www-data:www-data /var/www/printshop
sudo chmod -R 755 /var/www/printshop
```

## Step 7: Initialize the Database

```bash
# Make sure you're in the project directory
cd /var/www/printshop

# Activate the virtual environment if not already activated
source ../printshop_env/bin/activate

# Initialize the database
python init_db.py

# Create admin user (if needed)
python create_admin_user.py
```

## Step 8: Enable the Site and Restart Apache

```bash
sudo a2ensite printshop.conf
sudo systemctl restart apache2
```

## Step 9: Configure Nextcloud Integration (if needed)

Make sure your .env file includes the necessary Nextcloud credentials:

```
NEXTCLOUD_URL=https://your-nextcloud-instance.com
NEXTCLOUD_USERNAME=your_username
NEXTCLOUD_PASSWORD=your_secure_password
```

## Step 10: SSL Configuration (Recommended for Production)

For a secure connection, set up SSL with Let's Encrypt:

```bash
sudo apt-get install certbot python3-certbot-apache
sudo certbot --apache -d yourdomain.com
```

## Troubleshooting

### Check Apache Error Logs

```bash
sudo tail -f /var/log/apache2/printshop-error.log
```

### Check Application Status

```bash
sudo systemctl status apache2
```

### Common Issues

1. **WSGIProcessGroup error**: Make sure mod_wsgi is installed and enabled.
   ```bash
   sudo a2enmod wsgi
   ```

2. **Permission errors**: Check if Apache has proper permissions for all files.
   ```bash
   sudo chown -R www-data:www-data /var/www/printshop
   ```

3. **Database connection issues**: Verify the DATABASE_URL in your .env file.

4. **Module import errors**: Check if all Python dependencies are installed in the virtual environment.

## Regular Maintenance

### Updating the Application

```bash
# Pull the latest changes (if using Git)
cd /var/www/printshop
git pull

# Update dependencies
source ../printshop_env/bin/activate
pip install -r dependencies.txt

# Restart Apache
sudo systemctl restart apache2
```

### Database Backups

```bash
# Create a backup
pg_dump -U printshop_user printshop > /path/to/backup/printshop_$(date +%Y%m%d).sql

# Set up a cron job for regular backups
(crontab -l; echo "0 2 * * * pg_dump -U printshop_user printshop > /path/to/backup/printshop_$(date +%Y%m%d).sql") | crontab -
```