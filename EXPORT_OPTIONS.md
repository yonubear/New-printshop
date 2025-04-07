# Print Shop Management System - Export Options

This document provides information about the different export packages available for the Print Shop Management System.

## Available Export Packages

### Standard Export (Recommended for most users)
- **File**: `printshop_v4.1.1_download_20250402.zip` (163 KB)
- **Contents**: All application code, templates, database schema, documentation
- **Purpose**: For standard deployments, includes everything needed to run the application
- **Usage**: Extract and follow setup instructions in SETUP_GUIDE.md

### Complete Export with Database
- **File**: `printshop_complete_v4.1.1_20250402_174752.zip` (803 KB)
- **Contents**: All application code, templates, database with data, documentation
- **Purpose**: Full backup including database content - use for migrations or restoring a complete system
- **Usage**: Extract and run `python main.py` to start with existing data

### Minimal Export
- **File**: `printshop_export_final_v4.1.1_updated.zip` (163 KB)
- **Contents**: Core application code without database data
- **Purpose**: For clean installations or developers
- **Usage**: Extract, run `python init_db.py` to initialize the database, then `python main.py`

## Version History

- **v4.1.1** (Current): Improved database initialization, added missing qrcode dependency
- **v4.1**: Added comprehensive Excel template for data import, enhanced setup experience
- **v4.0**: Added profitability reporting, accounts receivable, payment tracking
- **v3.0**: Added material management, pull sheets with QR codes, customer proof approval

## Export File Naming Convention

- `printshop_v4.1.1_download_*.zip`: User-friendly download for v4.1.1
- `printshop_complete_v4.1.1_*.zip`: Complete package with database for v4.1.1
- `printshop_export_final_v4.1.1_*.zip`: Standard export (code only) for v4.1.1

## How to Use These Files

1. Download your preferred export package
2. Extract the files to your desired location
3. Follow the setup instructions in SETUP_GUIDE.md
4. Install dependencies: `pip install -r dependencies.txt`
5. Initialize the database (if needed): `python init_db.py`
6. Start the application: `python main.py`