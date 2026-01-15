from django.db import models
from django.contrib.auth.models import User

class StudentRequest(models.Model):
    STATUS_CHOICES = [
        ("SUBMITTED", "Submitted"),
        ("UNDER_REVIEW", "Under Review"),
        ("NEED_MORE_DOCS", "Need More Docs"),
        ("SENT_TO_HOD", "Sent To Head of Department"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_requests")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="SUBMITTED")
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.title} ({self.status})"


class RequestNote(models.Model):
    request = models.ForeignKey(StudentRequest, on_delete=models.CASCADE, related_name="notes")
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name="staff_notes")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class MissingDocument(models.Model):
    request = models.ForeignKey(StudentRequest, on_delete=models.CASCADE, related_name="missing_docs")
    doc_name = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)