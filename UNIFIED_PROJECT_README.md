# SCE Student Request Portal - Unified Project

This project has been unified from 4 separate branches into one cohesive Django application.

## Quick Start

### 1. Install Dependencies
```bash
pip install django
```

### 2. Run Migrations & Setup
**Option A:** Double-click `run_migrations.bat`

**Option B:** Run manually:
```bash
python manage.py makemigrations core requests_unified
python manage.py migrate
python populate.py
```

### 3. Start the Server
```bash
python manage.py runserver
```

### 4. Access the Application
Open: http://127.0.0.1:8000/auth/login/

## Demo Users

| Role | Email | Password |
|------|-------|----------|
| Student | student@ac.sce.ac.il | Student1! |
| Staff | staff@ac.sce.ac.il | Staff123! |
| Lecturer | lecturer@ac.sce.ac.il | Lecturer1! |
| Head of Dept | hod@ac.sce.ac.il | Head1234! |

## Project Structure

```
BS-FSE-2025-Team9/
├── campus_requests/          # Main Django project settings
│   ├── settings.py          # Unified settings
│   ├── urls.py              # Main URL routing
│   └── wsgi.py
├── core/                     # User model with 2FA
│   ├── models.py            # User, VerificationCode
│   ├── views.py             # Login with 2FA
│   └── urls.py
├── requests_unified/         # Request models
│   ├── models.py            # Request, StatusHistory, etc.
│   └── admin.py
├── students/                 # Student portal
│   ├── views.py             # Dashboard, submit request
│   └── urls.py
├── staff/                    # Staff dashboard
│   ├── views.py             # Add notes, request docs
│   └── urls.py
├── lecturers/                # Lecturer dashboard
│   ├── views.py             # Approve/reject/needs info
│   └── urls.py
├── head_of_dept/             # Department Head dashboard
│   ├── views.py             # Final approval, statistics
│   └── urls.py
├── templates/                # HTML templates
│   ├── base.html
│   ├── core/                # Login/verify templates
│   ├── students/            # Student templates
│   ├── staff/               # Staff templates
│   ├── lecturers/           # Lecturer templates
│   └── head_of_dept/        # HOD templates
├── static/                   # CSS, JS
├── media/                    # Uploaded files
├── manage.py
├── populate.py               # Demo data script
└── run_migrations.bat        # Quick setup script
```

## Features by Role

### Student
- Login with 2FA (email verification code)
- Submit requests (Study Approval, Appeal, Postponement, General)
- Track request status
- View status history and notes
- Edit profile

### Staff (Secretary)
- View all requests
- Add notes to requests
- Request missing documents
- Forward to Lecturer or HOD

### Lecturer
- View assigned requests
- Approve/Reject requests
- Mark as "Needs Info"
- Add feedback
- Forward to HOD

### Head of Department
- View pending final approvals
- Approve/Reject with final notes
- View statistics
- Add comments

## Request Workflow

```
Student submits → Staff reviews → Lecturer reviews → HOD approves/rejects
                      ↓                  ↓
               Request docs        Needs info
                      ↓                  ↓
                Student provides → Continue review
```

## API Endpoints (for HOD)

- `GET /head/api/pending-requests/` - Get pending requests
- `GET /head/api/statistics/` - Get statistics

## Authentication

All users use 2FA:
1. Enter email and password
2. Receive verification code via email
3. Enter code to complete login

## Notes

- Email must be from SCE domain (@ac.sce.ac.il)
- Password requirements: >6 chars, uppercase, lowercase, contains '!'
- Verification codes expire after 10 minutes
