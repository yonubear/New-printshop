# Print Shop Management System Deployment Guide

This export package contains everything needed to deploy the Print Shop Management System to your own server with Nextcloud integration.

## Quick Start

1. Extract this package to your server
2. Follow the instructions in `SETUP_GUIDE.md` to configure the application
3. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r dependencies.txt
```

## Nextcloud Configuration

To connect the application to your Nextcloud instance:

1. Create a dedicated user in Nextcloud for the application
2. Generate an app password for API access
3. Create a folder named 'print_orders' (or your chosen folder name)
4. Update the `.env` file with your Nextcloud credentials

## Configuration

Make sure to configure all required environment variables in the `.env` file. See `.env.template` for a list of available options.
