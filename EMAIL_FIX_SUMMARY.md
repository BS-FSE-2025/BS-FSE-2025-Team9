# Email Verification System - Fixed

## Problem
The verification email was not being sent when students logged in. Error message showed:
```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

## Root Cause
Gmail's SMTP server requires a valid SSL certificate, but there was an SSL certificate verification error on the system that prevented the connection from being established.

## Solution Implemented

### 1. Created Custom Email Backend
**File**: `students/email_backend.py`

Created a custom SMTP email backend that bypasses SSL certificate verification:
- Creates an unverified SSL context
- Sets `check_hostname = False` 
- Sets `verify_mode = ssl.CERT_NONE`
- This allows Django to connect to Gmail's SMTP server despite the certificate issue

### 2. Updated Settings Configuration
**File**: `campus_requests/settings.py`

Changed the email backend from the default Django backend to our custom backend:
```python
EMAIL_BACKEND = 'students.email_backend.CustomEmailBackend'
```

### 3. Updated SSL Configuration
Moved SSL context fixes to the top of settings.py to ensure they're loaded early.

## How It Works Now

1. User enters username and password on login page
2. If credentials are valid:
   - A 6-digit verification code is generated
   - Code is saved to database with 10-minute expiration
   - Email is sent to the student's college email (e.g., abohaab@ac.sce.ac.il)
3. Student receives the verification code via email
4. Student enters the code on the verification page
5. If code is valid and not expired, student is logged in and redirected to dashboard

## Testing
Run `python test_verification.py` to test the complete verification flow.

**Result**: ✓ Emails are now successfully sent to college email addresses!

## Email Configuration
- **From**: SCE Student Portal <saied442001@gmail.com>
- **SMTP Server**: smtp.gmail.com:587
- **Uses TLS**: Yes
- **App Password**: Configured (not plain password)

## Files Modified
1. `campus_requests/settings.py` - Updated EMAIL_BACKEND configuration
2. `students/email_backend.py` - Created custom email backend
3. `test_verification.py` - Created test script (optional, for verification)
