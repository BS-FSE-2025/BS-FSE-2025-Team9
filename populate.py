import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lecturer_system.settings")
django.setup()

from requests.models import Student, StudentRequest, Attachment

students = [
    ("STU-2024-001", "John Doe", "john.doe@university.edu"),
    ("STU-2024-002", "Jane Smith", "jane.smith@university.edu"),
    ("STU-2024-003", "Mike Johnson", "mike.johnson@university.edu"),
    ("STU-2024-004", "Sarah Williams", "sarah.williams@university.edu"),
    ("STU-2024-005", "David Brown", "david.brown@university.edu"),
]

types = ["Leave Request", "Certificate Request", "Extension Request", "Grade Appeal"]
statuses = ["pending", "approved", "rejected", "needs_info"]

courses = [
    "Intro to Computer Science",
    "Data Structures",
    "Logic & Set Theory",
    "Operating Systems",
    "Software Engineering",
]

descriptions = [
    "I need to request a leave of absence from January 15-20 due to a family emergency. I will catch up on missed coursework upon my return.",
    "Request for certificate of enrollment for visa application purposes.",
    "Requesting a 1-week extension for the final project due to unexpected technical issues.",
    "I would like to appeal my grade for the midterm exam. I believe there was a grading error in question 5.",
    "Medical leave request for surgery recovery. Expected duration: 2 weeks.",
]

# Clean and reseed (demo)
Attachment.objects.all().delete()
StudentRequest.objects.all().delete()
Student.objects.all().delete()

student_objs = []
for sid, name, email in students:
    student_objs.append(Student.objects.create(student_id=sid, name=name, email=email))

now = timezone.now()

for i in range(1, 7):
    st = random.choice(student_objs)

    r = StudentRequest.objects.create(
        request_id=f"REQ-{i:03d}",
        student=st,
        course_name=random.choice(courses),         # ✅ NEW
        request_type=random.choice(types),
        status=random.choice(statuses),
        description=random.choice(descriptions),
        lecturer_feedback="",
    )

    # OPTIONAL: randomize submitted time (last 30 days)
    random_days = random.randint(0, 30)
    random_hours = random.randint(0, 23)
    r.submitted_at = now - timedelta(days=random_days, hours=random_hours)
    r.save(update_fields=["submitted_at"])

    # Note: Attachment creation with actual files skipped in populate script
    # Attachments should be uploaded through the web interface
    # for k in range(random.randint(0, 2)):
    #     Attachment.objects.create(request=r, file=...)

print("✅ Database populated with demo data (including course + submitted time).")
