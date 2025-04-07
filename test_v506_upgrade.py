#!/usr/bin/env python3
"""
PrintShop v5.0.6 Upgrade Test Script

This script tests the update_v506_single_step.py script in a controlled environment
to verify that all migrations work correctly without affecting the production database.

Usage:
    python test_v506_upgrade.py
"""

import os
import sys
import logging
import tempfile
import shutil
import subprocess
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_environment():
    """Create a temporary test environment with a copy of required files"""
    logger.info("Creating test environment...")
    test_dir = tempfile.mkdtemp(prefix="printshop_v506_test_")
    logger.info(f"Test directory: {test_dir}")
    
    # Copy necessary files
    files_to_copy = [
        "update_v506_single_step.py",
        ".env"  # Assuming environment variables are in .env file
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(test_dir, file))
            logger.info(f"Copied {file} to test environment")
        else:
            logger.warning(f"Could not find {file} in current directory")
    
    return test_dir

def run_test(test_dir):
    """Run the upgrade script in test mode"""
    logger.info("Running upgrade script in test environment...")
    
    script_path = os.path.join(test_dir, "update_v506_single_step.py")
    
    # Set TEST_MODE environment variable
    os.environ['TEST_MODE'] = "1"
    
    # Change to test directory
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # Run the update script
        result = subprocess.run([sys.executable, script_path], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        if result.returncode == 0:
            logger.info("Update script executed successfully")
            logger.info("Output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
            return True
        else:
            logger.error(f"Update script failed with code {result.returncode}")
            logger.error("Error output:")
            for line in result.stderr.splitlines():
                logger.error(f"  {line}")
            return False
    except Exception as e:
        logger.error(f"Error running update script: {str(e)}")
        return False
    finally:
        # Reset environment variable and directory
        if 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']
        os.chdir(original_dir)

def cleanup(test_dir):
    """Clean up the test environment"""
    logger.info("Cleaning up test environment...")
    try:
        shutil.rmtree(test_dir)
        logger.info(f"Removed test directory: {test_dir}")
    except Exception as e:
        logger.error(f"Error cleaning up test directory: {str(e)}")

def main():
    """Main test function"""
    logger.info("=" * 80)
    logger.info("PrintShop v5.0.6 Upgrade Test")
    logger.info("=" * 80)
    
    test_dir = None
    success = False
    
    try:
        # Create test environment
        test_dir = create_test_environment()
        
        # Run test
        success = run_test(test_dir)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        success = False
    finally:
        # Cleanup
        if test_dir:
            cleanup(test_dir)
    
    # Report results
    logger.info("=" * 80)
    if success:
        logger.info("TEST PASSED: Update script works correctly")
        logger.info("The v5.0.6 update script is ready for deployment")
    else:
        logger.info("TEST FAILED: Update script encountered errors")
        logger.info("Please fix the issues before deploying")
    logger.info("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())