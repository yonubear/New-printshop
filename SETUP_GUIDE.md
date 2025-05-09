# Print Shop Management System Setup Guide

This guide will help you set up and deploy the Print Shop Management System on your own server with Nextcloud integration.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL or SQLite
- SMTP email server (for customer proof notifications)
- Nextcloud server installation (for file storage)

## Installation Steps

### 1. Clone or Extract Project Files

```bash
# If using Git
git clone https://your-repo-url/printshop-management.git
cd printshop-management

# If using ZIP file
unzip printshop_management.zip -d /path/to/destination
cd /path/to/destination
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r dependencies.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory based on the provided `.env.template`:

```bash
cp .env.template .env
```

Edit the `.env` file with your configuration:

```
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/printshop
# Or for SQLite: sqlite:///instance/printshop.db

# Nextcloud Configuration
NEXTCLOUD_URL=https://your-nextcloud-server.com
NEXTCLOUD_USERNAME=your_nextcloud_username
NEXTCLOUD_PASSWORD=your_nextcloud_password
NEXTCLOUD_FOLDER=print_orders

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com

# Application Configuration
SESSION_SECRET=your_random_secret_key
BASE_URL=https://your-application-url.com
```

### 5. Create a PostgreSQL Database (Optional)

If you're using PostgreSQL (recommended for production):

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create a database and user
CREATE DATABASE printshop;
CREATE USER printshop_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE printshop TO printshop_user;
\q
```

Update your `.env` file with the PostgreSQL connection string:

```
DATABASE_URL=postgresql://printshop_user:your_password@localhost/printshop
```

### 6. Initialize the Database

```bash
# This will create all necessary tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 7. Create an Admin User

```bash
python create_admin_user.py admin your_email@example.com your_strong_password
```

### 8. Running the Application

#### Development Mode

```bash
python main.py
```

#### Production Mode with Gunicorn

```bash
# Install Gunicorn if not already installed
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### 9. Setting Up with Nginx (Production)

For production deployment, it's recommended to use Nginx as a reverse proxy:

1. Install Nginx:
```bash
sudo apt-get install nginx
```

2. Create a Nginx configuration file:
```bash
sudo nano /etc/nginx/sites-available/printshop
```

3. Add the following configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/printshop /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

### 10. Setting Up SSL/TLS with Let's Encrypt

For secure HTTPS connections:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain a certificate
sudo certbot --nginx -d your-domain.com

# This will update your Nginx configuration automatically
```

## Nextcloud Configuration

1. Create a dedicated user in Nextcloud for the application
2. Generate an app password for API access
3. Create a folder named "print_orders" (or your chosen folder name)
4. Update the `.env` file with your Nextcloud credentials

## Email Configuration

For Gmail:

1. Enable 2-Step Verification in your Google Account
2. Generate an App Password for the application
3. Use the App Password in the MAIL_PASSWORD environment variable

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

1. Verify your PostgreSQL service is running:
```bash
sudo systemctl status postgresql
```

2. Check firewall settings if connecting to a remote database:
```bash
sudo ufw status
```

3. Ensure the database user has proper permissions:
```bash
sudo -u postgres psql -c "ALTER USER printshop_user WITH SUPERUSER;"
```

### Nextcloud Connection Issues

1. Verify the Nextcloud API endpoint is accessible:
```bash
curl https://your-nextcloud-server.com/ocs/v1.php/cloud/capabilities
```

2. Check for proper WebDAV configuration in Nextcloud.

3. Ensure your app password is correct and has not expired.

## Backup and Recovery

### Database Backup

```bash
# For PostgreSQL
pg_dump -U printshop_user -d printshop > backup.sql

# Restore from backup
psql -U printshop_user -d printshop < backup.sql
```

### Application Backup

Regularly back up these components:
1. The entire application code directory
2. The `.env` file with your configuration
3. The database
4. The uploaded files on your Nextcloud server