# Request Management System - Department Head Module

A comprehensive request management system with Department Head functionality for viewing, approving, and managing student requests.

## Features

### Department Head Features

1. **View Pending Requests**
   - Fetch and display all pending approval requests
   - Filter by date range (from/to dates)
   - Filter by request type (Study Approval, Appeal, Postponement, General)
   - Enforce approval-only visibility (only pending requests visible)
   - Real-time request loading with loading indicators

2. **Approve/Reject Requests**
   - Approve or reject pending requests
   - Add notes during approval/rejection
   - Automatic status updates
   - Approval action logging
   - Automatic notification to students

3. **Add Final Notes**
   - Add final notes that are visible to students
   - Notes are saved to request record
   - Notes displayed in student view
   - Notification sent to student when notes are added

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application:
   - Open your browser and navigate to `http://localhost:5000`
   - Use the quick login buttons or login with credentials:
     - Email: `head@example.com`
     - Password: `password`

## Quick Login

The system includes demo quick login buttons for:
- Student
- Secretary
- Lecturer
- Head of Dept

## API Endpoints

### Department Head Endpoints

- `GET /api/head/pending-requests` - Fetch pending requests (supports filtering)
  - Query parameters: `date_from`, `date_to`, `request_type`
  
- `POST /api/head/approve-request/<request_id>` - Approve or reject a request
  - Body: `{ "action": "approve" | "reject", "notes": "optional notes" }`
  
- `POST /api/head/add-final-notes/<request_id>` - Add final notes
  - Body: `{ "notes": "notes text" }`
  
- `GET /api/head/request-details/<request_id>` - Get detailed request information

## Database Schema

The system uses SQLite with the following main models:
- **User**: Users with roles (student, secretary, lecturer, head_of_dept)
- **Request**: Student requests with status, type, priority
- **ApprovalLog**: Log of all approval actions
- **Notification**: Notifications sent to users

## Security

- Role-based access control (RBAC)
- Session-based authentication
- Department Head role enforcement on all endpoints
- SQL injection protection via SQLAlchemy ORM

## Testing

The system includes sample data that is automatically created on first run:
- Demo users for each role
- Sample pending requests for testing

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Modern CSS with CSS Variables

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
