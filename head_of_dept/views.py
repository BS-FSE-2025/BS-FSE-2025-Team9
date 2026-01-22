"""
Head of Department views - Final approval, statistics, add final notes.
"""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from core.models import User
from requests_unified.models import (
    Request, StatusHistory, Notification, ApprovalLog, Comment
)


def hod_required(view_func):
    """Decorator to ensure user is Head of Department."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != User.ROLE_HEAD_OF_DEPT:
            messages.error(request, "Access denied. Head of Department account required.")
            return redirect('redirect_to_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def hod_required_api(view_func):
    """Decorator for API endpoints - returns JSON error."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        if request.user.role != User.ROLE_HEAD_OF_DEPT:
            return JsonResponse({'error': 'Forbidden - Head of Department access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

# BSSEF25T9-65: HOD – View Pending Requests (existing dashboard/api_pending_requests)
@login_required
@hod_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Head of Department dashboard - view pending requests for final approval."""
    status_filter = request.GET.get("status", "pending")
    request_type = request.GET.get("type", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    
    # Base query - requests sent to HOD or needing final approval
    requests_qs = Request.objects.filter(
        status=Request.STATUS_SENT_TO_HOD
    ).order_by("-created_at")
    
    # Apply filters
    if request_type:
        requests_qs = requests_qs.filter(request_type=request_type)
    
    if date_from:
        try:
            requests_qs = requests_qs.filter(created_at__date__gte=date_from)
        except:
            pass
    
    if date_to:
        try:
            requests_qs = requests_qs.filter(created_at__date__lte=date_to)
        except:
            pass
    
    # Statistics
    all_requests = Request.objects.all()
    total = all_requests.count()
    pending = Request.objects.filter(status=Request.STATUS_SENT_TO_HOD).count()
    approved = all_requests.filter(status=Request.STATUS_APPROVED).count()
    rejected = all_requests.filter(status=Request.STATUS_REJECTED).count()
    
    context = {
        "requests": requests_qs,
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "status_filter": status_filter,
        "request_type": request_type,
        "date_from": date_from,
        "date_to": date_to,
        "request_types": Request.REQUEST_TYPE_CHOICES,
    }
    return render(request, "head_of_dept/dashboard.html", context)


@login_required
@hod_required
def statistics(request: HttpRequest) -> HttpResponse:
    """View detailed statistics."""
    all_requests = Request.objects.all()
    
    total = all_requests.count()
    approved = all_requests.filter(status=Request.STATUS_APPROVED).count()
    rejected = all_requests.filter(status=Request.STATUS_REJECTED).count()
    pending = all_requests.filter(status=Request.STATUS_SENT_TO_HOD).count()
    in_progress = all_requests.filter(
        status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, 
                    Request.STATUS_SENT_TO_LECTURER, Request.STATUS_NEEDS_INFO]
    ).count()
    
    processed = approved + rejected
    approval_rate = (approved / processed * 100) if processed > 0 else 0
    rejection_rate = (rejected / processed * 100) if processed > 0 else 0
    
    # Stats by type
    type_stats = {}
    for req_type, label in Request.REQUEST_TYPE_CHOICES:
        type_requests = all_requests.filter(request_type=req_type)
        type_total = type_requests.count()
        type_approved = type_requests.filter(status=Request.STATUS_APPROVED).count()
        type_rejected = type_requests.filter(status=Request.STATUS_REJECTED).count()
        type_processed = type_approved + type_rejected
        
        type_stats[req_type] = {
            'label': label,
            'total': type_total,
            'approved': type_approved,
            'rejected': type_rejected,
            'pending': type_requests.filter(status=Request.STATUS_SENT_TO_HOD).count(),
            'approval_rate': round((type_approved / type_processed * 100), 2) if type_processed > 0 else 0,
        }
    
    context = {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "in_progress": in_progress,
        "processed": processed,
        "approval_rate": round(approval_rate, 2),
        "rejection_rate": round(rejection_rate, 2),
        "type_stats": type_stats,
    }
    return render(request, "head_of_dept/statistics.html", context)


@login_required
@hod_required
def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    """View request details."""
    req = get_object_or_404(Request, id=request_id)
    documents = req.documents.all()
    status_history = req.status_history.all()
    comments = req.comments.all()
    staff_notes = req.staff_notes.all()
    approval_logs = req.approval_logs.all()
    
    context = {
        "req": req,
        "documents": documents,
        "status_history": status_history,
        "comments": comments,
        "staff_notes": staff_notes,
        "approval_logs": approval_logs,
    }
    return render(request, "head_of_dept/request_detail.html", context)


@login_required
@hod_required
def approve_request(request: HttpRequest, request_id: int) -> HttpResponse:
    """Give final approval to a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        notes = request.POST.get("notes", "").strip()
        
        req.status = Request.STATUS_APPROVED
        req.head_of_dept = request.user
        if notes:
            req.final_notes = notes
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_APPROVED,
            description=f"Request approved by Head of Department. {notes}" if notes else "Request approved by Head of Department.",
            role=StatusHistory.ROLE_HEAD_OF_DEPT,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_APPROVED,
            notes=notes,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Great news! Your request '{req.title}' has been approved by the Head of Department!"
        )
        
        messages.success(request, "Request approved successfully!")
        return redirect("head_of_dept:dashboard")
    
    return redirect("head_of_dept:request_detail", request_id=request_id)


@login_required
@hod_required
def reject_request(request: HttpRequest, request_id: int) -> HttpResponse:
    """Reject a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        notes = request.POST.get("notes", "").strip()
        
        if not notes:
            messages.error(request, "Please provide a reason for rejection.")
            return redirect("head_of_dept:request_detail", request_id=request_id)
        
        req.status = Request.STATUS_REJECTED
        req.head_of_dept = request.user
        req.final_notes = notes
        req.save()
        
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_REJECTED,
            description=f"Request rejected by Head of Department. Reason: {notes}",
            role=StatusHistory.ROLE_HEAD_OF_DEPT,
            changed_by=request.user,
        )
        
        ApprovalLog.objects.create(
            request=req,
            approver=request.user,
            action=ApprovalLog.ACTION_REJECTED,
            notes=notes,
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Your request '{req.title}' has been rejected by the Head of Department. Reason: {notes}"
        )
        
        messages.success(request, "Request rejected.")
        return redirect("head_of_dept:dashboard")
    
    return redirect("head_of_dept:request_detail", request_id=request_id)

# BSSEF25T9-67: HOD – Add final notes visible to student (existing add_final_notes)
@login_required
@hod_required
def add_final_notes(request: HttpRequest, request_id: int) -> HttpResponse:
    """Add final notes to a request (visible to student)."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        notes = request.POST.get("notes", "").strip()
        
        if not notes:
            messages.error(request, "Please enter notes.")
            return redirect("head_of_dept:request_detail", request_id=request_id)
        
        req.final_notes = notes
        req.save()
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Final notes have been added to your request '{req.title}'."
        )
        
        messages.success(request, "Final notes added successfully.")
    
    return redirect("head_of_dept:request_detail", request_id=request_id)


@login_required
@hod_required
def add_comment(request: HttpRequest, request_id: int) -> HttpResponse:
    """Add a comment to a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        
        if not comment_text:
            messages.error(request, "Please enter a comment.")
            return redirect("head_of_dept:request_detail", request_id=request_id)
        
        Comment.objects.create(
            request=req,
            author=request.user,
            comment=comment_text,
        )
        
        messages.success(request, "Comment added.")
    
    return redirect("head_of_dept:request_detail", request_id=request_id)


# ============================================
# API ENDPOINTS (JSON responses)
# ============================================

@login_required
@hod_required_api
@require_http_methods(["GET"])
def api_pending_requests(request: HttpRequest) -> JsonResponse:
    """API: Get pending requests for HOD."""
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    request_type = request.GET.get('request_type')
    
    query = Request.objects.filter(status=Request.STATUS_SENT_TO_HOD)
    
    if date_from:
        try:
            query = query.filter(created_at__date__gte=date_from)
        except:
            pass
    
    if date_to:
        try:
            query = query.filter(created_at__date__lte=date_to)
        except:
            pass
    
    if request_type:
        query = query.filter(request_type=request_type)
    
    requests_list = []
    for req in query.order_by('-created_at'):
        requests_list.append({
            'id': req.id,
            'request_id': req.request_id,
            'title': req.title,
            'description': req.description,
            'request_type': req.request_type,
            'status': req.status,
            'priority': req.priority,
            'created_at': req.created_at.isoformat() if req.created_at else None,
            'student_name': req.student.get_full_name() or req.student.username,
            'student_email': req.student.email,
        })
    
    return JsonResponse({
        'success': True,
        'requests': requests_list,
        'count': len(requests_list)
    })


@login_required
@hod_required_api
@require_http_methods(["GET"])
def api_statistics(request: HttpRequest) -> JsonResponse:
    """API: Get statistics."""
    all_requests = Request.objects.all()
    
    total = all_requests.count()
    approved = all_requests.filter(status=Request.STATUS_APPROVED).count()
    rejected = all_requests.filter(status=Request.STATUS_REJECTED).count()
    pending = all_requests.filter(status=Request.STATUS_SENT_TO_HOD).count()
    in_progress = all_requests.filter(
        status__in=[Request.STATUS_NEW, Request.STATUS_IN_PROGRESS, 
                    Request.STATUS_SENT_TO_LECTURER, Request.STATUS_NEEDS_INFO]
    ).count()
    
    processed = approved + rejected
    approval_rate = (approved / processed * 100) if processed > 0 else 0
    rejection_rate = (rejected / processed * 100) if processed > 0 else 0
    
    type_stats = {}
    for req_type, label in Request.REQUEST_TYPE_CHOICES:
        type_requests = all_requests.filter(request_type=req_type)
        type_total = type_requests.count()
        type_approved = type_requests.filter(status=Request.STATUS_APPROVED).count()
        type_rejected = type_requests.filter(status=Request.STATUS_REJECTED).count()
        type_processed = type_approved + type_rejected
        
        type_stats[req_type] = {
            'total': type_total,
            'approved': type_approved,
            'rejected': type_rejected,
            'pending': type_requests.filter(status=Request.STATUS_SENT_TO_HOD).count(),
            'approval_rate': round((type_approved / type_processed * 100), 2) if type_processed > 0 else 0,
        }
    
    return JsonResponse({
        'success': True,
        'statistics': {
            'total': total,
            'approved': approved,
            'rejected': rejected,
            'pending': pending,
            'in_progress': in_progress,
            'processed': processed,
            'approval_rate': round(approval_rate, 2),
            'rejection_rate': round(rejection_rate, 2),
            'by_type': type_stats
        }
    })
