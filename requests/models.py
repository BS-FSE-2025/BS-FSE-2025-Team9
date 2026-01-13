from django.db import models

class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} ({self.student_id})"


class StudentRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("needs_info", "Needs Info"),
    ]

    request_id = models.CharField(max_length=20, unique=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="requests")

    # ✅ NEW: course
    course_name = models.CharField(max_length=150)

    request_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    description = models.TextField()

    # ✅ NEW: submitted time
    submitted_at = models.DateTimeField(auto_now_add=True)

    # lecturer side fields (if you already have them keep them)
    lecturer_feedback = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.request_id} - {self.student.student_id}"


class Attachment(models.Model):
    request = models.ForeignKey(StudentRequest, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/%d/", null=True, blank=True)
    filename = models.CharField(max_length=255, blank=True)  # Keep for backward compatibility
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        if self.file:
            return self.file.name
        return self.filename or "No file"

    def get_filename(self):
        if self.file:
            return self.file.name.split("/")[-1]
        return self.filename
