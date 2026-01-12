from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import User, Request, ApprovalLog, Notification, Comment

def require_head_of_dept(view_func):
    """Decorator to require head of department role"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        if request.user.role != 'head_of_dept':
            return JsonResponse({'error': 'Forbidden - Head of Department access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'head_of_dept':
            return redirect('head_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                if user.role == 'head_of_dept':
                    return JsonResponse({'success': True, 'role': user.role, 'redirect': '/head-dashboard/'})
                return JsonResponse({'success': True, 'role': user.role, 'redirect': '/dashboard/'})
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
        except:
            return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    return render(request, 'login.html')

def quick_login(request, role):
    """Quick login for demo purposes"""
    role_map = {
        'student': 'student',
        'secretary': 'secretary',
        'lecturer': 'lecturer',
        'head_of_dept': 'head_of_dept'
    }
    
    if role not in role_map:
        return redirect('login')
    
    try:
        user = User.objects.filter(role=role_map[role]).first()
        if user:
            login(request, user)
            if user.role == 'head_of_dept':
                return redirect('head_dashboard')
            return redirect('dashboard')
    except:
        pass
    
    return redirect('login')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def head_dashboard(request):
    if request.user.role != 'head_of_dept':
        return redirect('dashboard')
    return render(request, 'head_dashboard.html')

@login_required
@require_head_of_dept
@require_http_methods(["GET"])
def get_pending_requests(request):
    """Fetch pending approval requests with filtering"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    request_type = request.GET.get('request_type')
    
    # Base query - only pending requests
    query = Request.objects.filter(status='pending')
    
    # Apply filters
    if date_from:
        try:
            date_from_obj = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(created_at__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(created_at__lte=date_to_obj)
        except:
            pass
    
    if request_type:
        query = query.filter(request_type=request_type)
    
    requests_list = []
    for req in query:
        requests_list.append({
            'id': req.id,
            'title': req.title,
            'description': req.description,
            'request_type': req.request_type,
            'status': req.status,
            'priority': req.priority,
            'created_at': req.created_at.isoformat() if req.created_at else None,
            'updated_at': req.updated_at.isoformat() if req.updated_at else None,
            'final_notes': req.final_notes,
            'student_id': req.student.id,
            'student_name': req.student.name,
            'secretary_name': req.secretary.name if req.secretary else None,
            'lecturer_name': req.lecturer.name if req.lecturer else None,
        })
    
    return JsonResponse({
        'success': True,
        'requests': requests_list,
        'count': len(requests_list)
    })

@csrf_exempt
@login_required
@require_head_of_dept
@require_http_methods(["POST"])
def approve_request(request, request_id):
    """Approve or reject a request"""
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' or 'reject'
        notes = data.get('notes', '')
        
        if action not in ['approve', 'reject']:
            return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
        
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Only allow approval of pending requests
        if request_obj.status != 'pending':
            return JsonResponse({'success': False, 'error': 'Request is not pending'}, status=400)
        
        # Update request status
        request_obj.status = 'approved' if action == 'approve' else 'rejected'
        request_obj.head_of_dept = request.user
        request_obj.updated_at = timezone.now()
        request_obj.save()
        
        # Log approval action
        ApprovalLog.objects.create(
            request=request_obj,
            approver=request.user,
            action=action,
            notes=notes
        )
        
        # Create notification for student
        Notification.objects.create(
            user=request_obj.student,
            message=f'Your request "{request_obj.title}" has been {action}d by the Department Head.',
            request=request_obj
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Request {action}d successfully',
            'request': {
                'id': request_obj.id,
                'title': request_obj.title,
                'status': request_obj.status,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
@login_required
@require_head_of_dept
@require_http_methods(["POST"])
def add_final_notes(request, request_id):
    """Add final notes visible to student"""
    try:
        data = json.loads(request.body)
        notes = data.get('notes', '').strip()
        
        if not notes:
            return JsonResponse({'success': False, 'error': 'Notes cannot be empty'}, status=400)
        
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Update final notes
        request_obj.final_notes = notes
        request_obj.updated_at = timezone.now()
        request_obj.save()
        
        # Create notification for student
        Notification.objects.create(
            user=request_obj.student,
            message=f'Final notes have been added to your request "{request_obj.title}".',
            request=request_obj
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Final notes added successfully',
            'request': {
                'id': request_obj.id,
                'title': request_obj.title,
                'final_notes': request_obj.final_notes,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_head_of_dept
@require_http_methods(["GET"])
def get_request_details(request, request_id):
    """Get detailed information about a specific request"""
    request_obj = get_object_or_404(Request, id=request_id)
    
    # Get approval logs
    logs = ApprovalLog.objects.filter(request=request_obj)
    logs_list = []
    for log in logs:
        logs_list.append({
            'id': log.id,
            'action': log.action,
            'notes': log.notes,
            'created_at': log.created_at.isoformat() if log.created_at else None,
            'approver_name': log.approver.name,
        })
    
    # Get comments
    comments = Comment.objects.filter(request=request_obj)
    comments_list = []
    for comment in comments:
        comments_list.append({
            'id': comment.id,
            'comment': comment.comment,
            'author_name': comment.author.name,
            'author_role': comment.author.role,
            'created_at': comment.created_at.isoformat() if comment.created_at else None,
            'updated_at': comment.updated_at.isoformat() if comment.updated_at else None,
        })
    
    return JsonResponse({
        'success': True,
        'request': {
            'id': request_obj.id,
            'student_id': request_obj.student.id,
            'student_name': request_obj.student.name,
            'request_type': request_obj.request_type,
            'title': request_obj.title,
            'description': request_obj.description,
            'status': request_obj.status,
            'priority': request_obj.priority,
            'created_at': request_obj.created_at.isoformat() if request_obj.created_at else None,
            'updated_at': request_obj.updated_at.isoformat() if request_obj.updated_at else None,
            'final_notes': request_obj.final_notes,
            'secretary_name': request_obj.secretary.name if request_obj.secretary else None,
            'lecturer_name': request_obj.lecturer.name if request_obj.lecturer else None,
        },
        'approval_logs': logs_list,
        'comments': comments_list
    })

@login_required
@require_head_of_dept
@require_http_methods(["GET"])
def get_statistics(request):
    """Get approval/rejection statistics"""
    # Get all requests that have been processed (approved or rejected)
    all_requests = Request.objects.all()
    
    # Count by status
    total = all_requests.count()
    approved = all_requests.filter(status='approved').count()
    rejected = all_requests.filter(status='rejected').count()
    pending = all_requests.filter(status='pending').count()
    in_progress = all_requests.filter(status='in_progress').count()
    
    # Calculate rates (only for processed requests)
    processed = approved + rejected
    approval_rate = (approved / processed * 100) if processed > 0 else 0
    rejection_rate = (rejected / processed * 100) if processed > 0 else 0
    
    # Get statistics by request type
    type_stats = {}
    for req_type, _ in Request.REQUEST_TYPE_CHOICES:
        type_requests = all_requests.filter(request_type=req_type)
        type_total = type_requests.count()
        type_approved = type_requests.filter(status='approved').count()
        type_rejected = type_requests.filter(status='rejected').count()
        type_processed = type_approved + type_rejected
        
        type_stats[req_type] = {
            'total': type_total,
            'approved': type_approved,
            'rejected': type_rejected,
            'pending': type_requests.filter(status='pending').count(),
            'approval_rate': (type_approved / type_processed * 100) if type_processed > 0 else 0,
            'rejection_rate': (type_rejected / type_processed * 100) if type_processed > 0 else 0,
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

@csrf_exempt
@login_required
@require_head_of_dept
@require_http_methods(["POST"])
def add_comment(request, request_id):
    """Add a comment to a request"""
    try:
        data = json.loads(request.body)
        comment_text = data.get('comment', '').strip()
        
        if not comment_text:
            return JsonResponse({'success': False, 'error': 'Comment cannot be empty'}, status=400)
        
        request_obj = get_object_or_404(Request, id=request_id)
        
        # Create comment
        comment = Comment.objects.create(
            request=request_obj,
            author=request.user,
            comment=comment_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'comment': comment.comment,
                'author_name': comment.author.name,
                'author_role': comment.author.role,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
