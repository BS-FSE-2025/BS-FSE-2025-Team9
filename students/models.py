from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

from .validators import validate_student_email


class Student(AbstractUser):
    """
    Custom user model for students.
    Only SCE academic emails (@ac.sce.ac.il) are allowed.
    """

    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(), validate_student_email],
    )

    student_id = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        help_text="Internal student identifier as provided by the institution.",
    )

    def save(self, *args, **kwargs):
        if not self.student_id:
            import uuid
            self.student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class VerificationCode(models.Model):
    """
    Two-factor authentication verification codes.
    Code is sent to student's email during login.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="verification_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Code expires after 10 minutes
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if code is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    class Meta:
        ordering = ["-created_at"]


class Request(models.Model):
    """
    Core student request entity.
    """

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
    ]

    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SENT_TO_LECTURER = "sent_to_lecturer"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_SENT_TO_LECTURER, "Sent to Lecturer"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="requests")
    request_id = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=255)
    request_type = models.CharField(max_length=100)
    related_course = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    reason = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.request_id} - {self.title}"


class StatusHistory(models.Model):
    ROLE_STUDENT = "student"
    ROLE_SECRETARY = "secretary"
    ROLE_LECTURER = "lecturer"

    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_SECRETARY, "Secretary"),
        (ROLE_LECTURER, "Lecturer"),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=32, choices=Request.STATUS_CHOICES)
    description = models.CharField(max_length=255)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class StaffNote(models.Model):
    ROLE_SECRETARY = "secretary"
    ROLE_DEPARTMENT_HEAD = "department_head"

    ROLE_CHOICES = [
        (ROLE_SECRETARY, "Secretary"),
        (ROLE_DEPARTMENT_HEAD, "Department Head"),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="staff_notes")
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class RequestDocument(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="request_documents/")
    file_type = models.CharField(max_length=16)
    uploaded_by_student = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="notifications")
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]