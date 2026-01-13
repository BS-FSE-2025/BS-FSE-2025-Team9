"""
Admin user management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count

from core.models import User
from .decorators import admin_required


@admin_required
def dashboard(request):
    """Admin dashboard with user statistics."""
    # Get user counts by role
    total_users = User.objects.count()
    students = User.objects.filter(role=User.ROLE_STUDENT).count()
    secretaries = User.objects.filter(role=User.ROLE_SECRETARY).count()
    lecturers = User.objects.filter(role=User.ROLE_LECTURER).count()
    hods = User.objects.filter(role=User.ROLE_HEAD_OF_DEPT).count()
    admins = User.objects.filter(role=User.ROLE_ADMIN).count()
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'students': students,
        'secretaries': secretaries,
        'lecturers': lecturers,
        'hods': hods,
        'admins': admins,
        'recent_users': recent_users,
    }
    return render(request, 'management/dashboard.html', context)


@admin_required
def user_list(request):
    """List all users with search and filter."""
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(student_id__icontains=search) |
            Q(employee_id__icontains=search)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 15)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)
    
    context = {
        'users': users_page,
        'search': search,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'management/user_list.html', context)


@admin_required
def user_add(request):
    """Add a new user."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', User.ROLE_STUDENT)
        department = request.POST.get('department', '').strip()
        password = request.POST.get('password', '')
        student_id = request.POST.get('student_id', '').strip() or None
        employee_id = request.POST.get('employee_id', '').strip() or None
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exists():
            errors.append("A user with this email already exists.")
        
        if not first_name or not last_name:
            errors.append("First name and last name are required.")
        
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        
        # Validate Student ID format (exactly 9 digits) if provided
        if student_id:
            import re
            if not re.match(r'^\d{9}$', student_id):
                errors.append("Student ID must be exactly 9 digits.")
            elif User.objects.filter(student_id=student_id).exists():
                errors.append("This Student ID is already in use.")
        
        if employee_id and User.objects.filter(employee_id=employee_id).exists():
            errors.append("This Employee ID is already in use.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/user_form.html', {
                'form_data': request.POST,
                'role_choices': User.ROLE_CHOICES,
                'is_edit': False,
            })
        
        # Create username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department=department or None,
            student_id=student_id,
            employee_id=employee_id,
        )
        
        messages.success(request, f"User '{user.get_full_name()}' created successfully!")
        return redirect('management:user_list')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
        'is_edit': False,
    }
    return render(request, 'management/user_form.html', context)


@admin_required
def user_edit(request, user_id):
    """Edit an existing user."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', user.role)
        department = request.POST.get('department', '').strip()
        password = request.POST.get('password', '')  # Optional for edit
        student_id = request.POST.get('student_id', '').strip() or None
        employee_id = request.POST.get('employee_id', '').strip() or None
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not email:
            errors.append("Email is required.")
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            errors.append("A user with this email already exists.")
        
        if not first_name or not last_name:
            errors.append("First name and last name are required.")
        
        # Validate Student ID format (exactly 9 digits) if provided
        if student_id:
            import re
            if not re.match(r'^\d{9}$', student_id):
                errors.append("Student ID must be exactly 9 digits.")
            elif User.objects.filter(student_id=student_id).exclude(id=user.id).exists():
                errors.append("This Student ID is already in use.")
        
        if employee_id and User.objects.filter(employee_id=employee_id).exclude(id=user.id).exists():
            errors.append("This Employee ID is already in use.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/user_form.html', {
                'user': user,
                'form_data': request.POST,
                'role_choices': User.ROLE_CHOICES,
                'is_edit': True,
            })
        
        # Update user
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.department = department or None
        user.student_id = student_id
        user.employee_id = employee_id
        user.is_active = is_active
        
        if password:
            user.set_password(password)
        
        user.save()
        
        messages.success(request, f"User '{user.get_full_name()}' updated successfully!")
        return redirect('management:user_list')
    
    context = {
        'user': user,
        'role_choices': User.ROLE_CHOICES,
        'is_edit': True,
    }
    return render(request, 'management/user_form.html', context)


@admin_required
def user_delete(request, user_id):
    """Delete a user."""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user.id == request.user.id:
        messages.error(request, "You cannot delete your own account!")
        return redirect('management:user_list')
    
    if request.method == 'POST':
        user_name = user.get_full_name()
        user.delete()
        messages.success(request, f"User '{user_name}' has been deleted.")
        return redirect('management:user_list')
    
    context = {
        'user': user,
    }
    return render(request, 'management/user_delete.html', context)
