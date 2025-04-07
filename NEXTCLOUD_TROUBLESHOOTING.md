# Nextcloud Integration Troubleshooting Guide

This guide will help you diagnose and fix Nextcloud connectivity issues in the Print Shop Management System.

## Prerequisites

Before troubleshooting, ensure you have the following information ready:

1. Your Nextcloud server URL (e.g., `https://nextcloud.yourdomain.com`)
2. Your Nextcloud username
3. Your Nextcloud password
4. The folder name to use in Nextcloud (default: `print_orders`)

## Environment Configuration

Make sure your `.env` file contains the correct Nextcloud configuration:

```
NEXTCLOUD_URL=https://your-nextcloud-server.com
NEXTCLOUD_USERNAME=your_nextcloud_username
NEXTCLOUD_PASSWORD=your_nextcloud_password
NEXTCLOUD_FOLDER=print_orders
```

## Testing Your Nextcloud Connection

We've provided diagnostic tools to test your Nextcloud connection:

### General Connection Test
```
python test_nextcloud_connection.py
```

This will check:
- If your Nextcloud server is accessible
- If your credentials are valid
- If file upload/download/delete operations work correctly

### Username Format Verification
If you're having issues with username formats (particularly with email-format usernames), try:
```
python verify_nextcloud_username.py
```

This tool will:
- Test different username formats against your Nextcloud server
- Tell you which format is recognized by the server
- Provide recommendations for your .env file configuration

## Common Issues and Solutions

### 1. Connection Errors

**Problem**: Cannot connect to Nextcloud server
**Possible Causes**:
- Incorrect URL format
- Server is down or unreachable
- Network connectivity issues

**Solutions**:
- Ensure the URL begins with `https://` (or `http://` if not using SSL)
- Remove any trailing slashes from the URL
- Try accessing the URL in a browser to verify it's reachable
- Check network connectivity and firewall settings

### 2. Authentication Errors

**Problem**: Cannot authenticate with Nextcloud
**Possible Causes**:
- Incorrect username or password
- Email-format username not accepted by the server
- Account locked due to too many failed attempts
- Special characters in password not properly encoded
- Account doesn't exist on the server

**Solutions**:
- Verify your username and password by logging into the Nextcloud web interface
- If your username contains '@' (email format), try using just the part before '@'
  - For example, if your username is "user@example.com", try "user" instead
- Reset your password if necessary
- If using special characters in your password, ensure they're properly handled
- Create a new app password specifically for the Print Shop Management System
- Verify the account exists on the Nextcloud server

**Username Format Issues**:
If you see errors like "Principal with name user@example.com not found" or "Principal with name username not found":
1. Confirm the exact username needed by logging into the Nextcloud web interface
2. Check what username appears in the URL after you log in - this is typically your actual Nextcloud username
3. Update the NEXTCLOUD_USERNAME value in your .env file with this username
4. Some Nextcloud servers require just the username part without '@domain.com'

### 3. Permission Errors

**Problem**: Authentication works but file operations fail
**Possible Causes**:
- Insufficient permissions in Nextcloud
- Root folder doesn't exist
- Quota limits reached

**Solutions**:
- Check if the user has write permissions in Nextcloud
- Verify the root folder exists or can be created
- Check if you've reached your storage quota in Nextcloud

### 4. WebDAV Configuration Issues

**Problem**: Specific WebDAV operations fail
**Possible Causes**:
- WebDAV not properly enabled
- Server configuration issues
- Proxy or middleware interfering with WebDAV

**Solutions**:
- Ensure WebDAV is enabled in your Nextcloud instance
- Check Nextcloud server logs for specific errors
- Configure your server/proxy to properly handle WebDAV requests

### 5. SSL/TLS Certificate Issues

**Problem**: SSL certificate verification fails
**Possible Causes**:
- Self-signed certificate
- Expired certificate
- Certificate authority not recognized

**Solutions**:
- If using a self-signed certificate, configure the client to verify it
- Renew expired certificates
- Install a certificate from a recognized certificate authority

## Advanced Debugging

For more detailed debugging:

1. Enable DEBUG level logging
2. Check the Nextcloud server logs
3. Use network tools like Wireshark to inspect the traffic

## Specific Error Messages

### "Principal with name [username] not found"
This error suggests the username doesn't exist on the Nextcloud server or is not recognized in the format provided:
1. Verify that the account actually exists on the Nextcloud server
2. If using an email-format username (user@example.com), try using just the username part (user)
3. Log in to the Nextcloud web interface and check what username is shown in the URL
4. Ask your Nextcloud administrator to confirm the correct username format

### "Failed to create folder: 405 - Method Not Allowed"
This typically means the WebDAV endpoint doesn't support the MKCOL method or the user doesn't have permission to create directories.

### "Failed to upload file: 401 - Unauthorized"
Authentication failed. Check your username and password.

### "Failed to upload file: 403 - Forbidden"
The user is authenticated but doesn't have permission to write to the specified location.

### "Failed to upload file: 507 - Insufficient Storage"
The user has reached their storage quota on the Nextcloud server.

## Testing with curl

You can test basic Nextcloud connectivity with curl:

```bash
# Test authentication
curl -u username:password https://your-nextcloud-server.com/remote.php/dav/files/username/

# Test folder creation
curl -X MKCOL -u username:password https://your-nextcloud-server.com/remote.php/dav/files/username/print_orders/test_folder

# Test file upload
echo "test content" > test.txt
curl -T test.txt -u username:password https://your-nextcloud-server.com/remote.php/dav/files/username/print_orders/test.txt
```

## Need More Help?

If you continue to experience issues after trying these solutions, please check:

1. Your Nextcloud server logs
2. The application logs for more specific error messages
3. Consider temporarily enabling a more verbose logging level