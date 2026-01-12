from __future__ import annotations

import uuid
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings

from .forms import RequestDocumentForm, RequestForm
from .models import Notification, Request, StatusHistory, VerificationCode


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("students:login")


def login_with_verification(request: HttpRequest) -> HttpResponse:
    """
    Step 1: Username + Password authentication
    If successful, send verification code to email
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Generate 6-digit verification code
            code = str(random.randint(100000, 999999))
            
            # Delete old unused codes
            VerificationCode.objects.filter(
                student=user,
                is_used=False
            ).delete()
            
            # Create new verification code
            VerificationCode.objects.create(
                student=user,
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
                return redirect("students:verify_code")
                
            except Exception as e:
                messages.error(request, f"Failed to send verification code: {str(e)}")
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "students/login.html")


def verify_code(request: HttpRequest) -> HttpResponse:
    """
    Step 2: Verify the code sent to email
    """
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        messages.error(request, "Please login first")
        return redirect("students:login")
    
    from .models import Student
    user = Student.objects.get(id=user_id)
    
    if request.method == "POST":
        entered_code = request.POST.get("code", "").strip()
        
        # Find valid code
        verification = VerificationCode.objects.filter(
            student=user,
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
            
            messages.success(request, "Login successful!")
            return redirect("students:dashboard")
        else:
            messages.error(request, "Invalid or expired verification code")
    
    return render(request, "students/verify_code.html", {
        "email": user.email
    })


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    user = request.user

    if user.is_superuser or user.is_staff:
        requests_qs = Request.objects.all().order_by("-created_at")
        notifications = Notification.objects.all().order_by("-created_at")[:10]
    else:
        requests_qs = Request.objects.filter(student=user).order_by("-created_at")
        notifications = Notification.objects.filter(student=user).order_by("-created_at")[:10]

    status_filter = request.GET.get("status", "all")

    total_requests = requests_qs.count()
    new_count = requests_qs.filter(status=Request.STATUS_NEW).count()
    in_progress = requests_qs.filter(
        status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, Request.STATUS_SENT_TO_LECTURER]
    ).count()
    approved = requests_qs.filter(status=Request.STATUS_APPROVED).count()
    rejected = requests_qs.filter(status=Request.STATUS_REJECTED).count()

    if status_filter == "new":
        visible_requests = requests_qs.filter(status=Request.STATUS_NEW)
    elif status_filter == "in_progress":
        visible_requests = requests_qs.filter(
            status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, Request.STATUS_SENT_TO_LECTURER]
        )
    elif status_filter == "approved":
        visible_requests = requests_qs.filter(status=Request.STATUS_APPROVED)
    elif status_filter == "rejected":
        visible_requests = requests_qs.filter(status=Request.STATUS_REJECTED)
    else:
        status_filter = "all"
        visible_requests = requests_qs

    context = {
        "total_requests": total_requests,
        "new_count": new_count,
        "in_progress": in_progress,
        "approved": approved,
        "rejected": rejected,
        "requests": visible_requests,
        "status_filter": status_filter,
        "notifications": notifications,
        "is_admin": user.is_superuser or user.is_staff,
    }
    return render(request, "students/dashboard.html", context)


def _generate_request_id() -> str:
    return f"REQ-{uuid.uuid4().hex[:3].upper()}"


@login_required
@transaction.atomic
def submit_request(request: HttpRequest, request_type: str = None) -> HttpResponse:
    if request.method == "POST":
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        request_type_value = request.POST.get("request_type", "General")
        priority = request.POST.get("priority", "medium")
        
        if request_type_value == "Study Approval":
            course_name = request.POST.get("course_name", "")
            course_code = request.POST.get("course_code", "")
            semester = request.POST.get("semester", "")
            reason = request.POST.get("reason", "")
            
            if not title:
                title = f"Study Approval - {course_name}"
            description = f"Course Name: {course_name}\nCourse Code: {course_code}\nSemester: {semester}\nReason: {reason}"
            
        elif request_type_value == "Appeal":
            course_name = request.POST.get("course_name", "")
            grade_received = request.POST.get("grade_received", "")
            expected_grade = request.POST.get("expected_grade", "")
            reason = request.POST.get("reason", "")
            evidence = request.POST.get("evidence", "")
            
            if not title:
                title = f"Grade Appeal - {course_name}"
            description = f"Course Name: {course_name}\nGrade Received: {grade_received}\nExpected Grade: {expected_grade}\nReason: {reason}\nSupporting Evidence: {evidence}"
            
        elif request_type_value == "Postponement":
            semester = request.POST.get("semester", "")
            reason_type = request.POST.get("reason_type", "")
            explanation = request.POST.get("explanation", "")
            return_date = request.POST.get("return_date", "")
            
            if not title:
                title = f"Postponement Request - {semester}"
            description = f"Semester to Postpone: {semester}\nReason Type: {reason_type}\nExplanation: {explanation}\nExpected Return Date: {return_date if return_date else 'Not specified'}"
            
        elif request_type_value == "General":
            subject = request.POST.get("subject", "")
            category = request.POST.get("category", "")
            desc = request.POST.get("description", "")
            
            if not title:
                title = subject
            description = f"Category: {category}\nDescription: {desc}"

        new_request = Request.objects.create(
            student=request.user,
            request_id=_generate_request_id(),
            title=title,
            request_type=request_type_value,
            description=description,
            priority=priority,
            status=Request.STATUS_NEW
        )

        StatusHistory.objects.create(
            request=new_request,
            status=Request.STATUS_NEW,
            description="Request submitted by student.",
            role=StatusHistory.ROLE_STUDENT,
        )

        files = request.FILES.getlist("file")
        from .models import RequestDocument
        
        for f in files:
            RequestDocument.objects.create(
                request=new_request,
                file=f,
                file_type=f.content_type or "",
                uploaded_by_student=True,
            )

        Notification.objects.create(
            student=request.user,
            request=new_request,
            message=f"Your request '{title}' has been submitted successfully."
        )

        messages.success(request, "Your request has been submitted successfully!")
        return redirect("students:dashboard")

    initial_data = {}
    
    if request_type:
        type_map = {
            "study-approval": "Study Approval",
            "appeal": "Appeal",
            "postponement": "Postponement",
            "general": "General"
        }
        initial_data["request_type"] = type_map.get(request_type, "General")

    form = RequestForm(initial=initial_data)
    file_form = RequestDocumentForm()

    context = {
        "form": form,
        "file_form": file_form,
    }
    return render(request, "students/request_form.html", context)


@login_required
def request_detail(request: HttpRequest, request_id: str) -> HttpResponse:
    req = get_object_or_404(Request, request_id=request_id, student=request.user)
    status_history = req.status_history.all()
    staff_notes = req.staff_notes.all()
    documents = req.documents.all()

    context = {
        "request_obj": req,
        "status_history": status_history,
        "staff_notes": staff_notes,
        "documents": documents,
    }
    return render(request, "students/request_detail.html", context)


@login_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    user = request.user
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        
        errors = {}
        
        if not first_name:
            errors["first_name"] = "First name is required"
        
        if not last_name:
            errors["last_name"] = "Last name is required"
        
        if not email:
            errors["email"] = "Email is required"
        elif not email.endswith("@ac.sce.ac.il"):
            errors["email"] = "Email must be from SCE academic domain (@ac.sce.ac.il)"
        
        if current_password or new_password or confirm_password:
            if not current_password:
                errors["current_password"] = "Please enter your current password"
            elif not user.check_password(current_password):
                errors["current_password"] = "Current password is incorrect"
            
            if not new_password:
                errors["new_password"] = "Please enter a new password"
            else:
                if len(new_password) <= 6:
                    errors["new_password"] = "Password must be longer than 6 characters"
                elif not any(c.isupper() for c in new_password):
                    errors["new_password"] = "Password must contain at least one uppercase letter"
                elif not any(c.islower() for c in new_password):
                    errors["new_password"] = "Password must contain at least one lowercase letter"
                elif "!" not in new_password:
                    errors["new_password"] = "Password must include the '!' character"
            
            if new_password != confirm_password:
                errors["confirm_password"] = "Passwords do not match"
        
        if not errors:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            
            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)
            
            user.save()
            
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("students:profile_edit")
        else:

            
            for field, error in errors.items():
                messages.error(request, f"{field}: {error}")
    
    return render(request, "students/profile_edit.html")