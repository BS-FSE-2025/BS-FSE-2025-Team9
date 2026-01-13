"""
Staff/Secretary views - Review requests, add notes, request documents, forward to HOD.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import User
from requests_unified.models import (
    Request, StaffNote, MissingDocument, StatusHistory, Notification
)


def staff_required(view_func):
    """Decorator to ensure user is staff."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != User.ROLE_STAFF:
            messages.error(request, "Access denied. Staff account required.")
            return redirect('redirect_to_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@staff_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Staff dashboard - view all requests."""
    status_filter = request.GET.get("status", "all")
    
    requests_qs = Request.objects.all().order_by("-created_at")
    
    # Count statistics
    total = requests_qs.count()
    new_count = requests_qs.filter(status=Request.STATUS_NEW).count()
    in_progress = requests_qs.filter(status=Request.STATUS_IN_PROGRESS).count()
    needs_info = requests_qs.filter(status=Request.STATUS_NEEDS_INFO).count()
    
    # Filter
    if status_filter == "new":
        visible_requests = requests_qs.filter(status=Request.STATUS_NEW)
    elif status_filter == "in_progress":
        visible_requests = requests_qs.filter(status=Request.STATUS_IN_PROGRESS)
    elif status_filter == "needs_info":
        visible_requests = requests_qs.filter(status=Request.STATUS_NEEDS_INFO)
    else:
        status_filter = "all"
        visible_requests = requests_qs.exclude(
            status__in=[Request.STATUS_APPROVED, Request.STATUS_REJECTED]
        )
    
    context = {
        "requests": visible_requests,
        "total": total,
        "new_count": new_count,
        "in_progress": in_progress,
        "needs_info": needs_info,
        "status_filter": status_filter,
    }
    return render(request, "staff/dashboard.html", context)


@login_required
@staff_required
def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    """View request details."""
    req = get_object_or_404(Request, id=request_id)
    notes = req.staff_notes.all().order_by("-created_at")
    missing_docs = req.missing_docs.all().order_by("-created_at")
    documents = req.documents.all()
    status_history = req.status_history.all()
    
    context = {
        "req": req,
        "notes": notes,
        "missing_docs": missing_docs,
        "documents": documents,
        "status_history": status_history,
    }
    return render(request, "staff/request_detail.html", context)


@login_required
@staff_required
def add_note(request: HttpRequest, request_id: int) -> HttpResponse:
    """Add a note to a request."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            StaffNote.objects.create(
                request=req,
                author=request.user,
                role=StaffNote.ROLE_STAFF,
                note=text
            )
            
            # Update status if still new
            if req.status == Request.STATUS_NEW:
                req.status = Request.STATUS_IN_PROGRESS
                req.assigned_staff = request.user
                req.save()
                
                StatusHistory.objects.create(
                    request=req,
                    status=Request.STATUS_IN_PROGRESS,
                    description="Staff began reviewing the request.",
                    role=StatusHistory.ROLE_STAFF,
                    changed_by=request.user,
                )
            
            messages.success(request, "Note added successfully.")
        else:
            messages.error(request, "Please write a note first.")
    
    return redirect("staff:request_detail", request_id=req.id)


@login_required
@staff_required
def request_docs(request: HttpRequest, request_id: int) -> HttpResponse:
    """Request additional documents from student."""
    req = get_object_or_404(Request, id=request_id)
    
    if request.method == "POST":
        doc_name = request.POST.get("doc_name", "").strip()
        instructions = request.POST.get("instructions", "").strip()
        
        if doc_name:
            MissingDocument.objects.create(
                request=req,
                doc_name=doc_name,
                instructions=instructions,
                requested_by=request.user,
            )
            
            # Update status
            req.status = Request.STATUS_NEEDS_INFO
            req.save()
            
            StatusHistory.objects.create(
                request=req,
                status=Request.STATUS_NEEDS_INFO,
                description=f"Staff requested additional document: {doc_name}",
                role=StatusHistory.ROLE_STAFF,
                changed_by=request.user,
            )
            
            # Notify student
            Notification.objects.create(
                user=req.student,
                request=req,
                message=f"Additional document requested: {doc_name}. Please check your request details."
            )
            
            messages.success(request, "Additional documents request sent to student.")
        else:
            messages.error(request, "Please enter the missing document name.")
    
    return redirect("staff:request_detail", request_id=req.id)


@login_required
@staff_required
def send_to_lecturer(request: HttpRequest, request_id: int) -> HttpResponse:
    """Forward request to lecturer for review."""
    req = get_object_or_404(Request, id=request_id)
    
    # Check for unresolved missing documents
    if req.missing_docs.filter(resolved=False).exists():
        messages.error(request, "Cannot forward: there are pending missing documents.")
        return redirect("staff:request_detail", request_id=req.id)
    
    req.status = Request.STATUS_SENT_TO_LECTURER
    req.save()
    
    StatusHistory.objects.create(
        request=req,
        status=Request.STATUS_SENT_TO_LECTURER,
        description="Request forwarded to lecturer for review.",
        role=StatusHistory.ROLE_STAFF,
        changed_by=request.user,
    )
    
    # Notify student
    Notification.objects.create(
        user=req.student,
        request=req,
        message="Your request has been forwarded to a lecturer for review."
    )
    
    messages.success(request, "Request sent to lecturer.")
    return redirect("staff:request_detail", request_id=req.id)


@login_required
@staff_required
def send_to_hod(request: HttpRequest, request_id: int) -> HttpResponse:
    """Forward request directly to Head of Department."""
    req = get_object_or_404(Request, id=request_id)
    
    # Check for unresolved missing documents
    if req.missing_docs.filter(resolved=False).exists():
        messages.error(request, "Cannot forward: there are pending missing documents.")
        return redirect("staff:request_detail", request_id=req.id)
    
    req.status = Request.STATUS_SENT_TO_HOD
    req.save()
    
    StatusHistory.objects.create(
        request=req,
        status=Request.STATUS_SENT_TO_HOD,
        description="Request forwarded to Head of Department.",
        role=StatusHistory.ROLE_STAFF,
        changed_by=request.user,
    )
    
    # Notify student
    Notification.objects.create(
        user=req.student,
        request=req,
        message="Your request has been forwarded to the Head of Department."
    )
    
    messages.success(request, "Request sent to Head of Department.")
    return redirect("staff:request_detail", request_id=req.id)


@login_required
@staff_required
def resolve_doc(request: HttpRequest, doc_id: int) -> HttpResponse:
    """Mark a missing document as resolved."""
    doc = get_object_or_404(MissingDocument, id=doc_id)
    
    doc.resolved = True
    doc.resolved_at = timezone.now()
    doc.save()
    
    # Check if all missing docs are resolved
    req = doc.request
    if not req.missing_docs.filter(resolved=False).exists():
        # All docs resolved, update status back to in_progress
        if req.status == Request.STATUS_NEEDS_INFO:
            req.status = Request.STATUS_IN_PROGRESS
            req.save()
            
            StatusHistory.objects.create(
                request=req,
                status=Request.STATUS_IN_PROGRESS,
                description="All missing documents have been received.",
                role=StatusHistory.ROLE_STAFF,
                changed_by=request.user,
            )
    
    messages.success(request, "Document marked as received.")
    return redirect("staff:request_detail", request_id=doc.request.id)
