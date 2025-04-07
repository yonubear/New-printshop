# PrintShop v5.0.6 One-Step Upgrade Guide

This guide explains how to use the new one-step database upgrade process for PrintShop v5.0.6, which significantly simplifies the deployment process.

## What's New in v5.0.6?

PrintShop v5.0.6 introduces several important improvements:

* Fixed materials tracking for quotes
* Added n-up printing options in quote items
* Enhanced quote-to-order conversion
* Simplified database upgrade process (this guide)

## Before You Begin

1. **Backup Your Database**: Although the upgrade script attempts to create a backup automatically, a manual backup is recommended for safety.

2. **Download the Package**: Make sure you have downloaded the `printshop_v5.0.6_xxxxxxxx.zip` file.

## Quick Upgrade Steps

### Step 1: Extract the Package

Extract the `printshop_v5.0.6_xxxxxxxx.zip` file to your PrintShop installation directory.

### Step 2: Run the Upgrade Script

From your PrintShop root directory, run:

```bash
python update_v506_single_step.py
```

The script will:
* Check your environment
* Create a database backup (if possible)
* Perform all required database migrations
* Back up and update your code files
* Log all actions to a timestamped file

### Step 3: Restart Your Application

After the upgrade completes successfully, restart your PrintShop application to apply the changes.

## Verifying the Upgrade

After upgrading, verify that:

1. You can create and edit quotes with materials
2. Materials appear correctly on pull sheets
3. N-up printing options are available when creating quotes
4. You can successfully convert quotes to orders

## Troubleshooting

If you encounter issues during the upgrade:

1. Check the log file created in your PrintShop directory
2. Restore from your backup if necessary
3. Try running each migration script individually as described in RELEASE_NOTES_V5.0.6.md

## Advanced Testing (Optional)

For system administrators who want to test the upgrade process before applying it to production:

```bash
python test_v506_upgrade.py
```

This will simulate the upgrade process in a test environment without affecting your actual database.

## Need Help?

Refer to RELEASE_NOTES_V5.0.6.md and README.md for additional information.
