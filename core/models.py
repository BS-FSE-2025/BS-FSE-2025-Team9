from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta

from .validators import validate_sce_email


class User(AbstractUser):
    """
    Unified User model for all roles in the system.
    Supports 2FA via email verification codes.
    """
    
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
    
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(), validate_sce_email],
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    
    # For students - unique student ID
    student_id = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        help_text="Student ID as provided by the institution.",
    )
    
    # For staff/lecturers - employee ID
    employee_id = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        null=True,
        help_text="Employee ID for staff and lecturers.",
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    # Override to fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='core_user_set',
        related_query_name='core_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='core_user_set',
        related_query_name='core_user',
    )
    
    def save(self, *args, **kwargs):
        # Auto-generate student_id if role is student and not set
        if self.role == self.ROLE_STUDENT and not self.student_id:
            import uuid
            self.student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
        # Auto-generate employee_id if role is staff/lecturer/head and not set
        if self.role in [self.ROLE_STAFF, self.ROLE_LECTURER, self.ROLE_HEAD_OF_DEPT] and not self.employee_id:
            import uuid
            self.employee_id = f"EMP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT
    
    @property
    def is_staff_member(self):
        return self.role == self.ROLE_STAFF
    
    @property
    def is_lecturer(self):
        return self.role == self.ROLE_LECTURER
    
    @property
    def is_head_of_dept(self):
        return self.role == self.ROLE_HEAD_OF_DEPT
    
    def get_dashboard_url(self):
        """Return the appropriate dashboard URL based on role."""
        from django.urls import reverse
        if self.role == self.ROLE_STUDENT:
            return reverse('students:dashboard')
        elif self.role == self.ROLE_STAFF:
            return reverse('staff:dashboard')
        elif self.role == self.ROLE_LECTURER:
            return reverse('lecturers:dashboard')
        elif self.role == self.ROLE_HEAD_OF_DEPT:
            return reverse('head_of_dept:dashboard')
        return '/'


class VerificationCode(models.Model):
    """
    Two-factor authentication verification codes.
    Code is sent to user's email during login.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_codes"
    )
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
    
    def __str__(self):
        return f"Code for {self.user.email} - {'Used' if self.is_used else 'Active'}"
