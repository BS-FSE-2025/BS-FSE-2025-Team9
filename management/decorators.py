"""
Decorators for admin-only access control.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

from core.models import User


def admin_required(view_func):
    """
    Decorator that checks if the user is an admin or superuser.
    Redirects to home page if not authorized.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('core:login')
        
        # Check if user is admin or superuser
        if not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, "You don't have permission to access the admin area.")
            return redirect('redirect_to_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def course_manager_required(view_func):
    """
    Decorator that checks if the user can manage courses/degrees.
    Allowed roles: Admin, HOD, Secretary
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access this page.")
            return redirect('core:login')
        
        allowed_roles = [User.ROLE_ADMIN, User.ROLE_HEAD_OF_DEPT, User.ROLE_SECRETARY]
        if not (request.user.role in allowed_roles or request.user.is_superuser):
            messages.error(request, "You don't have permission to manage courses and degrees.")
            return redirect('redirect_to_dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper
