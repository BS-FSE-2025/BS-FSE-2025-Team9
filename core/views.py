"""
Core authentication views with 2FA for all user roles.
"""
import random
import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.conf import settings

from .models import User, VerificationCode
from requests_unified.models import Degree


def home(request: HttpRequest) -> HttpResponse:
    """Homepage / landing page."""
    if request.user.is_authenticated:
        return redirect("redirect_to_dashboard")
    return render(request, "core/home.html")


def signup(request: HttpRequest) -> HttpResponse:
    """Student registration page."""
    if request.user.is_authenticated:
        return redirect("redirect_to_dashboard")
    
    # Get available degrees
    degrees = Degree.objects.filter(is_active=True).order_by('name')
    form_data = {}
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        student_id = request.POST.get("student_id", "").strip()
        degree_id = request.POST.get("degree", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        
        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "student_id": student_id,
            "degree_id": degree_id,
        }
        
        # Validation
        errors = []
        
        if not first_name or not last_name:
            errors.append("First name and last name are required.")
        
        if not (email.endswith("@sce.ac.il") or email.endswith("@ac.sce.ac.il")):
            errors.append("Email must be a valid @sce.ac.il or @ac.sce.ac.il address.")
        
        if User.objects.filter(email=email).exists():
            errors.append("An account with this email already exists.")
        
        if not student_id:
            errors.append("Student ID is required.")
        elif not re.match(r'^\d{9}$', student_id):
            errors.append("Student ID must be exactly 9 digits.")
        elif User.objects.filter(student_id=student_id).exists():
            errors.append("This Student ID is already registered.")
        
        # Validate degree (REQUIRED for students)
        selected_degree = None
        if not degree_id:
            errors.append("Please select a degree program.")
        else:
            try:
                selected_degree = Degree.objects.get(id=degree_id, is_active=True)
            except Degree.DoesNotExist:
                errors.append("Please select a valid degree program.")
        
        # Password validation
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character.")
        
        if password != confirm_password:
            errors.append("Passwords do not match.")
        
        if errors:
            return render(request, "core/signup.html", {
                "error": " ".join(errors),
                "form_data": form_data,
                "degrees": degrees,
            })
        
        # Create user
        username = email.split("@")[0]
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="student",
            student_id=student_id,
            degree=selected_degree,
        )
        
        messages.success(request, "Account created successfully! Please sign in.")
        return redirect("core:login")
    
    return render(request, "core/signup.html", {"form_data": form_data, "degrees": degrees})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the user."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("core:home")


def login_with_verification(request: HttpRequest) -> HttpResponse:
    """
    Step 1: Username/Email + Password authentication
    If successful, send verification code to email
    """
    if request.user.is_authenticated:
        return redirect("redirect_to_dashboard")
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        
        # Try to authenticate with email as username
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            # Try finding user by email and authenticating
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        if user is not None:
            # Generate 6-digit verification code
            code = str(random.randint(100000, 999999))
            
            # Delete old unused codes
            VerificationCode.objects.filter(
                user=user,
                is_used=False
            ).delete()
            
            # Create new verification code
            VerificationCode.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Send email (uses console backend in dev - check terminal for code)
            try:
                send_mail(
                    subject='SCE Portal - Verification Code',
                    message=f'''
Hello {user.get_full_name() or user.username},

Your verification code is: {code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
SCE Student Portal
                    ''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                # Store user ID in session for verification step
                request.session['pending_user_id'] = user.id
                messages.success(request, f"Verification code sent to {user.email}")
                return redirect("core:verify_code")
                
            except Exception as e:
                messages.error(request, f"Failed to send verification code: {str(e)}")
        else:
            messages.error(request, "Invalid email or password")
    
    return render(request, "core/login.html")


def verify_code(request: HttpRequest) -> HttpResponse:
    """
    Step 2: Verify the code sent to email
    """
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("core:login")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please login again.")
        return redirect("core:login")
    
    if request.method == "POST":
        entered_code = request.POST.get("code", "").strip()
        
        # Find valid code
        verification = VerificationCode.objects.filter(
            user=user,
            code=entered_code,
            is_used=False
        ).first()
        
        if verification and verification.is_valid():
            # Mark code as used
            verification.is_used = True
            verification.save()
            
            # Log the user in
            login(request, user)
            
            # Clean up session (use pop to avoid KeyError if already deleted)
            request.session.pop('pending_user_id', None)
            
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect("redirect_to_dashboard")
        else:
            messages.error(request, "Invalid or expired verification code")
    
    return render(request, "core/verify_code.html", {
        "email": user.email
    })
