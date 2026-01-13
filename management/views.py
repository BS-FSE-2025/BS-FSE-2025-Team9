"""
Admin user management views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count

from core.models import User
from requests_unified.models import Degree, Course
from .decorators import admin_required, course_manager_required


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


# ============================================================
# DEGREE MANAGEMENT
# ============================================================

@course_manager_required
def degree_list(request):
    """List all degrees with search."""
    degrees = Degree.objects.all().order_by('name')
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        degrees = degrees.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    # Add student and course counts
    degrees = degrees.annotate(
        student_count=Count('students', distinct=True),
        course_count=Count('courses', distinct=True)
    )
    
    context = {
        'degrees': degrees,
        'search': search,
    }
    return render(request, 'management/degree_list.html', context)


@course_manager_required
def degree_add(request):
    """Add a new degree."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        is_active = request.POST.get('is_active') == 'on'
        
        errors = []
        
        if not name:
            errors.append("Degree name is required.")
        elif Degree.objects.filter(name__iexact=name).exists():
            errors.append("A degree with this name already exists.")
        
        if not code:
            errors.append("Degree code is required.")
        elif Degree.objects.filter(code__iexact=code).exists():
            errors.append("A degree with this code already exists.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/degree_form.html', {
                'form_data': request.POST,
                'is_edit': False,
            })
        
        degree = Degree.objects.create(
            name=name,
            code=code,
            is_active=is_active,
        )
        
        messages.success(request, f"Degree '{degree.name}' created successfully!")
        return redirect('management:degree_list')
    
    context = {
        'is_edit': False,
    }
    return render(request, 'management/degree_form.html', context)


@course_manager_required
def degree_edit(request, degree_id):
    """Edit an existing degree."""
    degree = get_object_or_404(Degree, id=degree_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        is_active = request.POST.get('is_active') == 'on'
        
        errors = []
        
        if not name:
            errors.append("Degree name is required.")
        elif Degree.objects.filter(name__iexact=name).exclude(id=degree.id).exists():
            errors.append("A degree with this name already exists.")
        
        if not code:
            errors.append("Degree code is required.")
        elif Degree.objects.filter(code__iexact=code).exclude(id=degree.id).exists():
            errors.append("A degree with this code already exists.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/degree_form.html', {
                'degree': degree,
                'form_data': request.POST,
                'is_edit': True,
            })
        
        degree.name = name
        degree.code = code
        degree.is_active = is_active
        degree.save()
        
        messages.success(request, f"Degree '{degree.name}' updated successfully!")
        return redirect('management:degree_list')
    
    context = {
        'degree': degree,
        'is_edit': True,
    }
    return render(request, 'management/degree_form.html', context)


@course_manager_required
def degree_delete(request, degree_id):
    """Delete a degree."""
    degree = get_object_or_404(Degree, id=degree_id)
    
    if request.method == 'POST':
        degree_name = degree.name
        degree.delete()
        messages.success(request, f"Degree '{degree_name}' has been deleted.")
        return redirect('management:degree_list')
    
    # Get related counts for warning
    student_count = degree.students.count()
    course_count = degree.courses.count()
    
    context = {
        'degree': degree,
        'student_count': student_count,
        'course_count': course_count,
    }
    return render(request, 'management/degree_delete.html', context)


# ============================================================
# COURSE MANAGEMENT
# ============================================================

@course_manager_required
def course_list(request):
    """List all courses with search and filters."""
    courses = Course.objects.all().order_by('code')
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        courses = courses.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )
    
    # Filter by degree
    degree_filter = request.GET.get('degree', '')
    if degree_filter:
        courses = courses.filter(degrees__id=degree_filter)
    
    # Add lecturer and request counts
    courses = courses.annotate(
        lecturer_count=Count('lecturers', distinct=True),
        request_count=Count('requests', distinct=True)
    ).distinct()
    
    degrees = Degree.objects.filter(is_active=True)
    
    context = {
        'courses': courses,
        'search': search,
        'degree_filter': degree_filter,
        'degrees': degrees,
    }
    return render(request, 'management/course_list.html', context)


@course_manager_required
def course_add(request):
    """Add a new course."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        degree_ids = request.POST.getlist('degrees')
        lecturer_ids = request.POST.getlist('lecturers')
        is_active = request.POST.get('is_active') == 'on'
        
        errors = []
        
        if not name:
            errors.append("Course name is required.")
        
        if not code:
            errors.append("Course code is required.")
        elif Course.objects.filter(code__iexact=code).exists():
            errors.append("A course with this code already exists.")
        
        if not degree_ids:
            errors.append("At least one degree must be selected.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/course_form.html', {
                'form_data': request.POST,
                'degrees': Degree.objects.filter(is_active=True),
                'lecturers': User.objects.filter(role=User.ROLE_LECTURER, is_active=True),
                'selected_degrees': degree_ids,
                'selected_lecturers': lecturer_ids,
                'is_edit': False,
            })
        
        course = Course.objects.create(
            name=name,
            code=code,
            is_active=is_active,
        )
        course.degrees.set(degree_ids)
        if lecturer_ids:
            course.lecturers.set(lecturer_ids)
        
        messages.success(request, f"Course '{course.code} - {course.name}' created successfully!")
        return redirect('management:course_list')
    
    context = {
        'degrees': Degree.objects.filter(is_active=True),
        'lecturers': User.objects.filter(role=User.ROLE_LECTURER, is_active=True),
        'is_edit': False,
    }
    return render(request, 'management/course_form.html', context)


@course_manager_required
def course_edit(request, course_id):
    """Edit an existing course."""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        degree_ids = request.POST.getlist('degrees')
        lecturer_ids = request.POST.getlist('lecturers')
        is_active = request.POST.get('is_active') == 'on'
        
        errors = []
        
        if not name:
            errors.append("Course name is required.")
        
        if not code:
            errors.append("Course code is required.")
        elif Course.objects.filter(code__iexact=code).exclude(id=course.id).exists():
            errors.append("A course with this code already exists.")
        
        if not degree_ids:
            errors.append("At least one degree must be selected.")
        
        if errors:
            messages.error(request, " ".join(errors))
            return render(request, 'management/course_form.html', {
                'course': course,
                'form_data': request.POST,
                'degrees': Degree.objects.filter(is_active=True),
                'lecturers': User.objects.filter(role=User.ROLE_LECTURER, is_active=True),
                'selected_degrees': degree_ids,
                'selected_lecturers': lecturer_ids,
                'is_edit': True,
            })
        
        course.name = name
        course.code = code
        course.is_active = is_active
        course.save()
        course.degrees.set(degree_ids)
        course.lecturers.set(lecturer_ids)
        
        messages.success(request, f"Course '{course.code} - {course.name}' updated successfully!")
        return redirect('management:course_list')
    
    context = {
        'course': course,
        'degrees': Degree.objects.filter(is_active=True),
        'lecturers': User.objects.filter(role=User.ROLE_LECTURER, is_active=True),
        'selected_degrees': list(course.degrees.values_list('id', flat=True)),
        'selected_lecturers': list(course.lecturers.values_list('id', flat=True)),
        'is_edit': True,
    }
    return render(request, 'management/course_form.html', context)


@course_manager_required
def course_delete(request, course_id):
    """Delete a course."""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_name = f"{course.code} - {course.name}"
        course.delete()
        messages.success(request, f"Course '{course_name}' has been deleted.")
        return redirect('management:course_list')
    
    # Get related counts for warning
    request_count = course.requests.count()
    
    context = {
        'course': course,
        'request_count': request_count,
    }
    return render(request, 'management/course_delete.html', context)
