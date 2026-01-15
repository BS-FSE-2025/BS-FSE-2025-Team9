"""
Student portal views - Dashboard, submit requests, track status, profile management.
"""
from __future__ import annotations

import uuid
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import User
from requests_unified.models import (
    Request, StatusHistory, Notification, RequestDocument, Course
)


def student_required(view_func):
    """Decorator to ensure user is a student."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != User.ROLE_STUDENT:
            messages.error(request, "Access denied. Student account required.")
            return redirect('redirect_to_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@student_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Student dashboard - view all requests and notifications."""
    user = request.user
    
    requests_qs = Request.objects.filter(student=user).order_by("-created_at")
    notifications = Notification.objects.filter(user=user).order_by("-created_at")[:10]
    
    status_filter = request.GET.get("status", "all")
    
    total_requests = requests_qs.count()
    new_count = requests_qs.filter(status=Request.STATUS_NEW).count()
    in_progress = requests_qs.filter(
        status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, 
                    Request.STATUS_SENT_TO_LECTURER, Request.STATUS_SENT_TO_HOD,
                    Request.STATUS_NEEDS_INFO]
    ).count()
    approved = requests_qs.filter(status=Request.STATUS_APPROVED).count()
    rejected = requests_qs.filter(status=Request.STATUS_REJECTED).count()
    
    if status_filter == "new":
        visible_requests = requests_qs.filter(status=Request.STATUS_NEW)
    elif status_filter == "in_progress":
        visible_requests = requests_qs.filter(
            status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, 
                        Request.STATUS_SENT_TO_LECTURER, Request.STATUS_SENT_TO_HOD,
                        Request.STATUS_NEEDS_INFO]
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
    }
    return render(request, "students/dashboard.html", context)


def _generate_request_id() -> str:
    return f"REQ-{uuid.uuid4().hex[:8].upper()}"


@login_required
@student_required
@transaction.atomic
def submit_request(request: HttpRequest, request_type: str = None) -> HttpResponse:
    """Submit a new request."""
    user = request.user
    
    # Get courses for the student's degree
    if user.degree:
        courses = Course.objects.filter(degrees=user.degree, is_active=True).order_by('code')
    else:
        courses = Course.objects.filter(is_active=True).order_by('code')
    
    if request.method == "POST":
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        request_type_value = request.POST.get("request_type", "General")
        priority = request.POST.get("priority", "medium")
        course_id = request.POST.get("course", "")
        
        # Get selected course
        selected_course = None
        if course_id:
            try:
                selected_course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                pass
        
        if request_type_value == "Study Approval":
            semester = request.POST.get("semester", "")
            reason = request.POST.get("reason", "")
            
            course_display = f"{selected_course.code} - {selected_course.name}" if selected_course else "Not specified"
            if not title:
                title = f"Study Approval - {course_display}"
            description = f"Course: {course_display}\nSemester: {semester}\nReason: {reason}"
            
        elif request_type_value == "Appeal":
            grade_received = request.POST.get("grade_received", "")
            expected_grade = request.POST.get("expected_grade", "")
            reason = request.POST.get("reason", "")
            evidence = request.POST.get("evidence", "")
            
            course_display = f"{selected_course.code} - {selected_course.name}" if selected_course else "Not specified"
            if not title:
                title = f"Grade Appeal - {course_display}"
            description = f"Course: {course_display}\nGrade Received: {grade_received}\nExpected Grade: {expected_grade}\nReason: {reason}\nSupporting Evidence: {evidence}"
            
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
                title = subject or "General Request"
            
            if selected_course:
                description = f"Course: {selected_course.code} - {selected_course.name}\nCategory: {category}\nDescription: {desc}"
            else:
                description = f"Category: {category}\nDescription: {desc}"
        
        new_request = Request.objects.create(
            student=request.user,
            title=title,
            request_type=request_type_value,
            description=description,
            priority=priority,
            status=Request.STATUS_NEW,
            course=selected_course,
        )
        
        StatusHistory.objects.create(
            request=new_request,
            status=Request.STATUS_NEW,
            description="Request submitted by student.",
            role=StatusHistory.ROLE_STUDENT,
            changed_by=request.user,
        )
        
        # Handle file uploads
        files = request.FILES.getlist("file")
        for f in files:
            RequestDocument.objects.create(
                request=new_request,
                file=f,
                file_type=f.content_type or "",
                uploaded_by=request.user,
                uploaded_by_student=True,
            )
        
        Notification.objects.create(
            user=request.user,
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
    
    context = {
        "initial_data": initial_data,
        "courses": courses,
    }
    return render(request, "students/request_form.html", context)


@login_required
@student_required
def request_detail(request: HttpRequest, request_id: str) -> HttpResponse:
    """View details of a specific request."""
    req = get_object_or_404(Request, request_id=request_id, student=request.user)
    status_history = req.status_history.all()
    staff_notes = req.staff_notes.all()
    documents = req.documents.all()
    comments = req.comments.all()
    
    context = {
        "request_obj": req,
        "status_history": status_history,
        "staff_notes": staff_notes,
        "documents": documents,
        "comments": comments,
    }
    return render(request, "students/request_detail.html", context)


@login_required
@student_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    """Edit user profile."""
    user = request.user
    
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        messages.success(request, "Your account information has been updated successfully.")

        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        
        errors = {}
        
        if not first_name:
            errors["first_name"] = "First name is required"
        
        if not last_name:
            errors["last_name"] = "Last name is required"
        
        # Password change validation
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
            
            if new_password:
                user.set_password(new_password)
                update_session_auth_hash(request, user)
            
            user.save()
            
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("students:profile_edit")
        else:
            for field, error in errors.items():
                messages.error(request, f"{error}")
    
    return render(request, "students/profile_edit.html")
