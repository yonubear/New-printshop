#!/usr/bin/env python3
"""
PrintShop Manager v5.0.1 Database Update Script

This script provides a comprehensive database update for v5.0.1.
It runs both the general PostgreSQL database check and the specific
v5.0.1 verification to ensure all columns are properly added.

Usage:
    python update_v501_database.py
"""

import os
import sys
import logging
import importlib.util
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('db_updater')

def run_script(script_path, args=None):
    """Run a Python script with arguments."""
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        # Construct command
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        # Run script
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script execution failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False

def main():
    """Run database update scripts in sequence."""
    logger.info("Starting PrintShop Manager v5.0.1 database update")
    
    # Step 1: Run the PostgreSQL database checker with fix option
    logger.info("Step 1: Running general PostgreSQL database check...")
    check_script = "check_postgresql_database.py"
    if not run_script(check_script, ["--fix"]):
        logger.warning("General database check encountered issues but continuing...")
    
    # Step 2: Run the v5.0.1 verifier with fix option
    logger.info("Step 2: Running v5.0.1 specific verification...")
    verify_script = "verify_v501_database.py"
    if not run_script(verify_script, ["--fix"]):
        logger.error("Failed to update database for v5.0.1")
        return 1
    
    # Step 3: Check for any square footage column scripts and run them
    logger.info("Step 3: Running additional square footage column scripts...")
    sqft_scripts = ["add_sqft_pricing_complete.py", "add_sqft_pricing_columns.py"]
    
    for script in sqft_scripts:
        if os.path.exists(script):
            logger.info(f"Running {script}...")
            if not run_script(script):
                logger.warning(f"Script {script} encountered issues but continuing...")
    
    logger.info("Database update completed successfully")
    logger.info("Your PrintShop Manager database is now ready for v5.0.1")
    logger.info("You can now start your application with 'python main.py'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())