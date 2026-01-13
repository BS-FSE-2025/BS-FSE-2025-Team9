#!/usr/bin/env python
"""
Test script for verification code sending
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_requests.settings')
django.setup()

from students.models import Student, VerificationCode
import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

# Get the student
student = Student.objects.get(username="ahmad2024")
print(f"Testing with student: {student.username} ({student.email})")

# Generate verification code
code = str(random.randint(100000, 999999))
print(f"\nGenerated verification code: {code}")

# Delete old codes
VerificationCode.objects.filter(student=student, is_used=False).delete()

# Create new code
vc = VerificationCode.objects.create(
    student=student,
    code=code,
    expires_at=timezone.now() + timedelta(minutes=10)
)
print(f"✓ Verification code saved to database")

# Send email
try:
    send_mail(
        subject='SCE Portal - Verification Code',
        message=f'''
Hello {student.get_full_name() or student.username},

Your verification code is: {code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
SCE Student Portal
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student.email],
        fail_silently=False,
    )
    print(f"✓ Verification email sent successfully to {student.email}!")
except Exception as e:
    print(f"✗ Failed to send email: {str(e)}")
