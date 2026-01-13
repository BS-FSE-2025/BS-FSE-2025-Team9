import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Request(models.Model):
    """
    Unified Request model combining all fields from the 4 branches.
    Supports the full workflow: Student -> Staff -> Lecturer -> HOD
    """
    
    # Request Types
    TYPE_STUDY_APPROVAL = 'Study Approval'
    TYPE_APPEAL = 'Appeal'
    TYPE_POSTPONEMENT = 'Postponement'
    TYPE_GENERAL = 'General'
    
    REQUEST_TYPE_CHOICES = [
        (TYPE_STUDY_APPROVAL, 'Study Approval'),
        (TYPE_APPEAL, 'Appeal'),
        (TYPE_POSTPONEMENT, 'Postponement'),
        (TYPE_GENERAL, 'General'),
    ]
    
    # Combined Status choices from all branches
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_SENT_TO_LECTURER = 'sent_to_lecturer'
    STATUS_SENT_TO_HOD = 'sent_to_hod'
    STATUS_NEEDS_INFO = 'needs_info'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_SENT_TO_LECTURER, 'Sent to Lecturer'),
        (STATUS_SENT_TO_HOD, 'Sent to Head of Department'),
        (STATUS_NEEDS_INFO, 'Needs More Information'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]
    
    # Priority choices
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]
    
    # Core fields
    request_id = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_requests',
        limit_choices_to={'role': 'student'},
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPE_CHOICES,
        default=TYPE_GENERAL,
    )
    
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
    )
    
    # Optional course info (for Study Approval, Appeal)
    course_name = models.CharField(max_length=150, blank=True)
    related_course = models.CharField(max_length=255, blank=True)
    
    # Additional reason field
    reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Assignment tracking
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_assigned_requests',
        limit_choices_to={'role': 'staff'},
    )
    
    assigned_lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lecturer_assigned_requests',
        limit_choices_to={'role': 'lecturer'},
    )
    
    head_of_dept = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hod_assigned_requests',
        limit_choices_to={'role': 'head_of_dept'},
    )
    
    # Final notes from department head
    final_notes = models.TextField(blank=True, null=True)
    
    # Lecturer feedback
    lecturer_feedback = models.TextField(blank=True, default="")
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_id} - {self.title}"
    
    def get_status_badge_class(self):
        """Return CSS class for status badge."""
        return f"badge--{self.status}"


class StatusHistory(models.Model):
    """Track all status changes for a request."""
    
    ROLE_STUDENT = 'student'
    ROLE_STAFF = 'staff'
    ROLE_LECTURER = 'lecturer'
    ROLE_HEAD_OF_DEPT = 'head_of_dept'
    
    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_STAFF, 'Staff'),
        (ROLE_LECTURER, 'Lecturer'),
        (ROLE_HEAD_OF_DEPT, 'Head of Department'),
    ]
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=32, choices=Request.STATUS_CHOICES)
    description = models.CharField(max_length=255)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Status histories'
    
    def __str__(self):
        return f"{self.request.request_id} -> {self.status}"


class StaffNote(models.Model):
    """Notes added by staff or department head."""
    
    ROLE_STAFF = 'staff'
    ROLE_HEAD_OF_DEPT = 'head_of_dept'
    
    ROLE_CHOICES = [
        (ROLE_STAFF, 'Staff'),
        (ROLE_HEAD_OF_DEPT, 'Head of Department'),
    ]
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='staff_notes'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_notes'
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Note by {self.author} on {self.request.request_id}"


class RequestDocument(models.Model):
    """Documents attached to requests."""
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    file = models.FileField(upload_to='request_documents/')
    file_type = models.CharField(max_length=50, blank=True)
    filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents'
    )
    uploaded_by_student = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return self.filename or "No file"
    
    def get_filename(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return self.filename


class MissingDocument(models.Model):
    """Track documents that staff requests from students."""
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='missing_docs'
    )
    doc_name = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Missing: {self.doc_name} for {self.request.request_id}"


class Comment(models.Model):
    """Comments on requests (from any role)."""
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.request.request_id}"


class ApprovalLog(models.Model):
    """Log of all approval/rejection actions."""
    
    ACTION_APPROVED = 'approved'
    ACTION_REJECTED = 'rejected'
    ACTION_NEEDS_INFO = 'needs_info'
    ACTION_FORWARDED = 'forwarded'
    
    ACTION_CHOICES = [
        (ACTION_APPROVED, 'Approved'),
        (ACTION_REJECTED, 'Rejected'),
        (ACTION_NEEDS_INFO, 'Requested More Info'),
        (ACTION_FORWARDED, 'Forwarded'),
    ]
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_actions'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.approver} {self.action} {self.request.request_id}"


class Notification(models.Model):
    """Notifications sent to users."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user}: {self.message[:50]}"
