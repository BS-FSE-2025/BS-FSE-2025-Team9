"""
Lecturer views - Review requests, approve/reject, add feedback, mark as needs info.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.db.models import Q

from core.models import User
from requests_unified.models import (
    Request, StatusHistory, Notification, ApprovalLog, Comment
)


def lecturer_required(view_func):
    """Decorator to ensure user is a lecturer."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != User.ROLE_LECTURER:
            messages.error(request, "Access denied. Lecturer account required.")
            return redirect('redirect_to_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@lecturer_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Lecturer dashboard - view assigned/pending requests."""
    user = request.user
    status_filter = request.GET.get("status", "all")
    
    # Get courses taught by this lecturer
    taught_courses = user.taught_courses.all()
    
    # Get requests that are:
    # 1. Sent to lecturer status AND in one of their courses, OR
    # 2. Explicitly assigned to this lecturer
    requests_qs = Request.objects.filter(
        Q(
            status__in=[Request.STATUS_SENT_TO_LECTURER, Request.STATUS_NEEDS_INFO],
            course__in=taught_courses
        ) |
        Q(assigned_lecturer=user)
    ).distinct().order_by("-created_at")
    
    # Count statistics
    total = requests_qs.count()
    pending = requests_qs.filter(status=Request.STATUS_SENT_TO_LECTURER).count()
    needs_info = requests_qs.filter(status=Request.STATUS_NEEDS_INFO).count()
    
    # Filter
    if status_filter == "pending":
        visible_requests = requests_qs.filter(status=Request.STATUS_SENT_TO_LECTURER)
    elif status_filter == "needs_info":
        visible_requests = requests_qs.filter(status=Request.STATUS_NEEDS_INFO)
    else:
        status_filter = "all"
        visible_requests = requests_qs
    
    context = {
        "requests": visible_requests,
        "total": total,
        "pending": pending,
        "needs_info": needs_info,
        "status_filter": status_filter,
        "taught_courses": taught_courses,
    }
    return render(request, "lecturers/dashboard.html", context)


@login_required
@lecturer_required
def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    """View request details."""
    req = get_object_or_404(Request, id=request_id)
    documents = req.documents.all()
    status_history = req.status_history.all()
    comments = req.comments.all()
    staff_notes = req.staff_notes.all()
    
    context = {
        "req": req,
        "documents": documents,
        "status_history": status_history,
        "comments": comments,
        "staff_notes": staff_notes,
    }
    return render(request, "lecturers/request_detail.html", context)


@login_required
@lecturer_required
def approve_request(request: HttpRequest, request_id: int) -> HttpResponse:
    """Approve a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        
        req.status = Request.STATUS_APPROVED
        req.assigned_lecturer = request.user
        req.lecturer_feedback = feedback
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_APPROVED,
            description=f"Request approved by lecturer. {feedback}" if feedback else "Request approved by lecturer.",
            role=StatusHistory.ROLE_LECTURER,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_APPROVED,
            notes=feedback,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Your request '{req.title}' has been approved by a lecturer!"
        )
        
        messages.success(request, "Request approved successfully!")
        return redirect("lecturers:dashboard")
    
    return redirect("lecturers:request_detail", request_id=request_id)


@login_required
@lecturer_required
def reject_request(request: HttpRequest, request_id: int) -> HttpResponse:
    """Reject a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        
        if not feedback:
            messages.error(request, "Please provide a reason for rejection.")
            return redirect("lecturers:request_detail", request_id=request_id)
        
        req.status = Request.STATUS_REJECTED
        req.assigned_lecturer = request.user
        req.lecturer_feedback = feedback
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_REJECTED,
            description=f"Request rejected by lecturer. Reason: {feedback}",
            role=StatusHistory.ROLE_LECTURER,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_REJECTED,
            notes=feedback,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Your request '{req.title}' has been rejected. Reason: {feedback}"
        )
        
        messages.success(request, "Request rejected.")
        return redirect("lecturers:dashboard")
    
    return redirect("lecturers:request_detail", request_id=request_id)


@login_required
@lecturer_required
def needs_info(request: HttpRequest, request_id: int) -> HttpResponse:
    """Mark request as needing more information."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        
        if not feedback:
            messages.error(request, "Please specify what information is needed.")
            return redirect("lecturers:request_detail", request_id=request_id)
        
        req.status = Request.STATUS_NEEDS_INFO
        req.assigned_lecturer = request.user
        req.lecturer_feedback = feedback
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_NEEDS_INFO,
            description=f"Lecturer requested more information: {feedback}",
            role=StatusHistory.ROLE_LECTURER,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_NEEDS_INFO,
            notes=feedback,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"More information needed for your request '{req.title}': {feedback}"
        )
        
        messages.success(request, "Request marked as needing more information.")
        return redirect("lecturers:dashboard")
    
    return redirect("lecturers:request_detail", request_id=request_id)


@login_required
@lecturer_required
def forward_to_hod(request: HttpRequest, request_id: int) -> HttpResponse:
    """Forward request to Head of Department for final decision."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        feedback = request.POST.get("feedback", "").strip()
        
        req.status = Request.STATUS_SENT_TO_HOD
        req.assigned_lecturer = request.user
        if feedback:
            req.lecturer_feedback = feedback
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_SENT_TO_HOD,
            description=f"Forwarded to Head of Department by lecturer. {feedback}" if feedback else "Forwarded to Head of Department by lecturer.",
            role=StatusHistory.ROLE_LECTURER,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_FORWARDED,
            notes=feedback,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Your request '{req.title}' has been forwarded to the Head of Department."
        )
        
        messages.success(request, "Request forwarded to Head of Department.")
        return redirect("lecturers:dashboard")
    
    return redirect("lecturers:request_detail", request_id=request_id)
