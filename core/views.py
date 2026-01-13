"""
Core authentication views with 2FA for all user roles.
"""
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.conf import settings

from .models import User, VerificationCode


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the user."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


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
            
            # Send email
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
                return redirect("verify_code")
                
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
        return redirect("login")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please login again.")
        return redirect("login")
    
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
            
            # Clean up session
            del request.session['pending_user_id']
            
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect("redirect_to_dashboard")
        else:
            messages.error(request, "Invalid or expired verification code")
    
    return render(request, "core/verify_code.html", {
        "email": user.email
    })
