# Django Setup Guide

This project has been converted to Django. Follow these steps to set it up.

## Installation

1. **Install Django dependencies:**
   ```bash
   pip install -r requirements_django.txt
   ```

2. **Run migrations to create database tables:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create demo data (users and sample requests):**
   ```bash
   python manage.py create_demo_data
   ```

4. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   - Open your browser and go to: `http://localhost:8000`
   - Use quick login buttons or login with:
     - Email: `head@example.com`
     - Password: `password`

## Project Structure

```
project_dh/
├── manage.py                    # Django management script
├── request_management/         # Main project directory
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   └── wsgi.py                 # WSGI configuration
├── requests_app/               # Main app
│   ├── models.py               # Database models
│   ├── views.py                # View functions
│   ├── urls.py                 # App URL configuration
│   ├── admin.py                # Admin configuration
│   └── management/
│       └── commands/
│           └── create_demo_data.py  # Demo data command
├── templates/                   # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── head_dashboard.html
│   └── dashboard.html
└── static/                      # Static files
    └── css/
        └── style.css
```

## Key Differences from Flask Version

1. **Custom User Model**: Uses Django's AbstractUser with additional fields (role, name, department)
2. **URL Routing**: Uses Django's URL patterns instead of Flask routes
3. **Templates**: Uses Django template syntax (`{% %}` and `{{ }}`)
4. **Static Files**: Uses Django's static file handling
5. **Authentication**: Uses Django's built-in authentication system
6. **Database**: Uses Django ORM instead of SQLAlchemy

## API Endpoints

All endpoints remain the same:
- `GET /api/head/pending-requests/` - Fetch pending requests
- `POST /api/head/approve-request/<id>/` - Approve/reject request
- `POST /api/head/add-final-notes/<id>/` - Add final notes
- `GET /api/head/request-details/<id>/` - Get request details

## Admin Interface

Access Django admin at: `http://localhost:8000/admin/`

You can manage:
- Users
- Requests
- Approval Logs
- Notifications

## Features

✅ All Flask features converted to Django
✅ Custom User model with roles
✅ Department Head dashboard
✅ Pending requests with filtering
✅ Approve/Reject functionality
✅ Final notes feature
✅ Notification system
✅ Approval logging

## Troubleshooting

**Issue: No module named 'requests_app'**
- Make sure you're in the project root directory
- Check that `requests_app` is in `INSTALLED_APPS` in `settings.py`

**Issue: Migration errors**
- Delete `db.sqlite3` and `requests_app/migrations/` (except `__init__.py`)
- Run `python manage.py makemigrations` again
- Run `python manage.py migrate`

**Issue: Template not found**
- Check that `TEMPLATES` in `settings.py` includes `BASE_DIR / 'templates'`
- Verify template files are in the `templates/` directory

**Issue: Static files not loading**
- Run `python manage.py collectstatic` (for production)
- Check `STATICFILES_DIRS` in `settings.py`
- Make sure `{% load static %}` is at the top of templates

## Development

To run in development mode with auto-reload:
```bash
python manage.py runserver
```

To run on a specific port:
```bash
python manage.py runserver 8001
```

## Production Deployment

For production:
1. Set `DEBUG = False` in `settings.py`
2. Update `ALLOWED_HOSTS`
3. Set a secure `SECRET_KEY`
4. Use a production database (PostgreSQL recommended)
5. Configure static file serving
6. Use a production WSGI server (Gunicorn, uWSGI)
