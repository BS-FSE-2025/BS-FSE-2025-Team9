"""
Unified URL configuration for Student Request Management System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def redirect_to_dashboard(request):
    """Redirect authenticated users to their role-specific dashboard."""
    if not request.user.is_authenticated:
        return redirect('core:home')
    
    user = request.user
    if user.role == 'student':
        return redirect('students:dashboard')
    elif user.role == 'secretary':
        return redirect('staff:dashboard')
    elif user.role == 'lecturer':
        return redirect('lecturers:dashboard')
    elif user.role == 'head_of_dept':
        return redirect('head_of_dept:dashboard')
    
    # Default fallback
    return redirect('students:dashboard')


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    
    # Core pages (home, auth)
    path("", include("core.urls")),
    
    # Dashboard redirect for authenticated users
    path("dashboard/", redirect_to_dashboard, name="redirect_to_dashboard"),
    
    # Role-specific dashboards
    path("students/", include("students.urls")),
    path("staff/", include("staff.urls")),
    path("lecturers/", include("lecturers.urls")),
    path("head/", include("head_of_dept.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
