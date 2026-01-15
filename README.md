# Student Forms Request Management System

A comprehensive web-based request management system designed to digitize and automate student academic and administrative requests, enabling efficient submission, tracking, review, and approval by all academic roles.
## Features

### Project Description
The Student Forms Request Management System replaces manual, paper-based student forms with a centralized digital platform.
It allows students to submit requests online and enables academic secretaries, lecturers, and department heads to review, process, and approve requests through a structured workflow with full transparency and notifications.

 **User Roles & Functionalities**
 
  ## User Roles & Functionalities
   **Student**
   -Secure login and logout
   -Submit new requests with attachments
   -Track request status in real time
   -View request history and staff notes
   -Receive notifications for every status update

   **Academic Secretary**
   -View assigned student requests
   -Review and validate submitted documents
   -Add notes or request additional documents
   -Update request status
   -Forward requests to lecturers or department heads

   **Lecturer**
   -View requests related to their courses
   -Review academic details
   -Add professional comments or recommendations
   -Forward reviewed requests for final approval

   **Head of Department**

   -View all pending approval requests
   -Filter requests by date and type
   -Approve or reject requests
   -Add final notes visible to students
   -Monitor request statistics and processing performance

## Features

**System Features**
 
 1. **Authentication & Security**
 -Secure login/logout system
 -Role-Based Access Control (RBAC)
 -Session-based authentication
 -Protected API endpoints

 2. **Digital Request Submission**
 -Multiple request types:
 -Study Approval
 -Appeal
 -Postponement
 -General Request
 -File upload and document management
 -Input validation

 3. **Request Processing Workflow**
 -Multi-role approval flow
 -Automatic status updates
 -Request forwarding between roles
 -Full request history tracking

 4. **Notification System**
 -Submission confirmation
 -Status change notifications
 -Approval/rejection alerts
 -Final notes notifications

 5. **Dashboards & Management**
 -Student dashboard with request summary
 -Staff and lecturer request management views
 -Department head analytics and statistics
 -Exportable reports (future support)

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
     - Email: `admin@ac.sce.ac.il.com`
     - Password: `admin`

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

- **Backend**: Flask (Python),Django
- **Database**: SQLite with SQLAlchemy ORM,Django
- **Frontend**: HTML5, CSS3 ,Django
- **Styling**: Modern CSS with CSS Variables

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
