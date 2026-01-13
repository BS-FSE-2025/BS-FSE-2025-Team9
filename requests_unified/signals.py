"""
Signal handlers for handling orphaned requests when courses or lecturers are deleted.
Routes pending requests to Head of Department.
Also handles automatic initialization of required data (degrees).
"""
import sys
from django.db.models.signals import pre_delete, m2m_changed, post_migrate
from django.dispatch import receiver
from django.conf import settings

from core.models import User
from .models import Course, Request, StatusHistory, Notification, Degree


# =============================================================================
# DEFAULT DEGREES - These are automatically created when the app starts
# =============================================================================
DEFAULT_DEGREES = [
    {'name': 'Software Engineering', 'code': 'SE'},
    {'name': 'Computer Science', 'code': 'CS'},
    {'name': 'Electrical Engineering', 'code': 'EE'},
    {'name': 'Industrial Engineering', 'code': 'IE'},
    {'name': 'Civil Engineering', 'code': 'CE'},
]


def is_testing():
    """Check if we're running tests."""
    return 'test' in sys.argv or 'pytest' in sys.modules


def initialize_degrees(verbose=True):
    """
    Ensure all default degrees exist in the database.
    Called automatically after migrations (but not during tests).
    """
    created_count = 0
    for degree_data in DEFAULT_DEGREES:
        degree, created = Degree.objects.get_or_create(
            code=degree_data['code'],
            defaults={'name': degree_data['name'], 'is_active': True}
        )
        if created:
            created_count += 1
            if verbose:
                print(f"  ✓ Created degree: {degree.name} ({degree.code})")
    
    if created_count > 0 and verbose:
        print(f"  → Initialized {created_count} default degree(s)")
    
    return created_count


@receiver(post_migrate)
def create_default_degrees(sender, **kwargs):
    """
    Automatically create default degrees after migrations run.
    This ensures degrees always exist in the database.
    Skip during tests to allow test isolation.
    """
    # Only run for our app
    if sender.name == 'requests_unified':
        # Skip during tests - tests create their own degrees
        if is_testing():
            return
        
        try:
            initialize_degrees()
        except Exception:
            # Silently fail if database isn't ready
            pass


def route_requests_to_hod(requests_queryset, reason):
    """
    Route pending requests to HOD status.
    """
    pending_statuses = [
        Request.STATUS_NEW,
        Request.STATUS_IN_PROGRESS,
        Request.STATUS_SENT_TO_LECTURER,
        Request.STATUS_NEEDS_INFO,
    ]
    
    for req in requests_queryset.filter(status__in=pending_statuses):
        # Update status to sent to HOD
        req.status = Request.STATUS_SENT_TO_HOD
        req.save(update_fields=['status'])
        
        # Create status history entry
        StatusHistory.objects.create(
            request=req,
            status=Request.STATUS_SENT_TO_HOD,
            description=f"Request automatically routed to HOD: {reason}",
            role=StatusHistory.ROLE_STAFF,
            changed_by=None,  # System action
        )
        
        # Notify student
        Notification.objects.create(
            user=req.student,
            request=req,
            message=f"Your request has been automatically routed to the Head of Department due to: {reason}"
        )


@receiver(pre_delete, sender=Course)
def handle_course_deletion(sender, instance, **kwargs):
    """
    When a course is deleted, route all its pending requests to HOD.
    """
    route_requests_to_hod(
        instance.requests.all(),
        f"Course '{instance.code} - {instance.name}' was removed"
    )


@receiver(m2m_changed, sender=Course.lecturers.through)
def handle_lecturer_removed_from_course(sender, instance, action, pk_set, **kwargs):
    """
    When a lecturer is removed from a course, route requests assigned to them to HOD.
    """
    if action == "pre_remove":
        for lecturer_id in pk_set:
            try:
                lecturer = User.objects.get(id=lecturer_id)
                # Get requests for this course that are assigned to this lecturer
                affected_requests = Request.objects.filter(
                    course=instance,
                    assigned_lecturer=lecturer
                )
                route_requests_to_hod(
                    affected_requests,
                    f"Lecturer '{lecturer.get_full_name()}' was removed from course '{instance.code}'"
                )
            except User.DoesNotExist:
                pass


@receiver(pre_delete, sender=User)
def handle_lecturer_deletion(sender, instance, **kwargs):
    """
    When a lecturer is deleted, route all their assigned requests to HOD.
    """
    if instance.role == User.ROLE_LECTURER:
        route_requests_to_hod(
            Request.objects.filter(assigned_lecturer=instance),
            f"Lecturer '{instance.get_full_name()}' account was removed"
        )
