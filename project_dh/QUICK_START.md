# Quick Start Guide

## Installation & Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`
   - The database and demo users will be created automatically on first run

## Quick Login

Use the quick login buttons on the login page:
- **Head of Dept** - Access Department Head dashboard
- **Student** - Access student view
- **Secretary** - Access secretary view
- **Lecturer** - Access lecturer view

Or login with credentials:
- Email: `head@example.com`
- Password: `password`

## Department Head Features

### 1. View Pending Requests
- Navigate to the Head Dashboard
- All pending requests are displayed automatically
- Use the filter section to:
  - Filter by date range (From/To dates)
  - Filter by request type (Study Approval, Appeal, Postponement, General)
- Click "Apply Filters" to update the list
- Click "Clear" to reset filters

### 2. Approve/Reject Requests
- On any request card, click:
  - **Approve** (green button) - Approve the request
  - **Reject** (red button) - Reject the request
- Enter optional notes when prompted
- The request status updates immediately
- A notification is sent to the student

### 3. Add Final Notes
- Click **View Details** on any request card
- Scroll to the "Add Final Notes" section
- Enter notes that will be visible to the student
- Click **Save Notes**
- Notes are saved and a notification is sent to the student

## Testing

Run the test script to verify all functionality:
```bash
python test_head_functionality.py
```

Make sure the Flask server is running before executing tests.

## Troubleshooting

**Issue: Database errors**
- Delete `request_management.db` and restart the server
- The database will be recreated automatically

**Issue: Port already in use**
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

**Issue: Module not found**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## Features Checklist

✅ View pending requests with filtering
✅ Approve requests with notes
✅ Reject requests with notes
✅ Add final notes visible to students
✅ Approval action logging
✅ Student notifications
✅ Role-based access control
✅ Responsive UI design

## Support

For detailed documentation, see:
- `README.md` - General project documentation
- `DEPARTMENT_HEAD_FEATURES.md` - Detailed feature documentation
