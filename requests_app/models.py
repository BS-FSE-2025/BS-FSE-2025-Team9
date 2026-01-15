from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('secretary', 'Secretary'),
        ('lecturer', 'Lecturer'),
        ('head_of_dept', 'Head of Department'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='student')
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    # Override to fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    def __str__(self):
        return f"{self.name} ({self.role})"

class Request(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('Study Approval', 'Study Approval'),
        ('Appeal', 'Appeal'),
        ('Postponement', 'Postponement'),
        ('General', 'General'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_progress', 'In Progress'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_requests')
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    secretary = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='secretary_requests')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lecturer_requests')
    head_of_dept = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='head_requests')
    final_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class ApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='approval_logs')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.approver.name} {self.action} {self.request.title}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_notifications', null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.name}"

class Comment(models.Model):
    """Comments added by Department Head on requests"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.name} on {self.request.title}"
