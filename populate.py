#!/usr/bin/env python
"""
Populate script - Creates demo users and sample requests for testing.
Run: python populate.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_requests.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from requests_unified.models import Request, StatusHistory, Notification

User = get_user_model()


def create_users():
    """Create demo users for all roles."""
    print("Creating demo users...")
    
    users_data = [
        {
            'username': 'student1',
            'email': 'student@ac.sce.ac.il',
            'password': 'Student1!',
            'first_name': 'John',
            'last_name': 'Student',
            'role': User.ROLE_STUDENT,
        },
        {
            'username': 'student2',
            'email': 'student2@ac.sce.ac.il',
            'password': 'Student2!',
            'first_name': 'Jane',
            'last_name': 'Student',
            'role': User.ROLE_STUDENT,
        },
        {
            'username': 'secretary1',
            'email': 'secretary@ac.sce.ac.il',
            'password': 'Secretary1!',
            'first_name': 'Sarah',
            'last_name': 'Secretary',
            'role': User.ROLE_SECRETARY,
        },
        {
            'username': 'lecturer1',
            'email': 'lecturer@ac.sce.ac.il',
            'password': 'Lecturer1!',
            'first_name': 'Dr. Michael',
            'last_name': 'Professor',
            'role': User.ROLE_LECTURER,
        },
        {
            'username': 'hod1',
            'email': 'hod@ac.sce.ac.il',
            'password': 'Head1234!',
            'first_name': 'Prof. David',
            'last_name': 'Department Head',
            'role': User.ROLE_HEAD_OF_DEPT,
        },
        {
            'username': 'admin1',
            'email': 'admin@ac.sce.ac.il',
            'password': 'Admin123!',
            'first_name': 'System',
            'last_name': 'Administrator',
            'role': User.ROLE_ADMIN,
        },
    ]
    
    created_users = {}
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'username': user_data['username'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
            }
        )
        if created:
            user.set_password(user_data['password'])
            user.save()
            print(f"  Created: {user.email} ({user.get_role_display()})")
        else:
            print(f"  Exists: {user.email} ({user.get_role_display()})")
        
        created_users[user_data['role']] = user
    
    return created_users


def create_sample_requests(users):
    """Create sample requests in various statuses."""
    print("\nCreating sample requests...")
    
    student = users.get(User.ROLE_STUDENT)
    if not student:
        print("  No student found, skipping requests")
        return
    
    requests_data = [
        {
            'title': 'Course Overload Request',
            'description': 'I would like to take 6 courses this semester to complete my degree requirements on time.',
            'request_type': Request.TYPE_STUDY_APPROVAL,
            'priority': Request.PRIORITY_HIGH,
            'status': Request.STATUS_NEW,
        },
        {
            'title': 'Grade Appeal - Data Structures',
            'description': 'Course Name: Data Structures\nGrade Received: 72\nExpected Grade: 85\nReason: I believe my final exam was graded incorrectly.',
            'request_type': Request.TYPE_APPEAL,
            'priority': Request.PRIORITY_MEDIUM,
            'status': Request.STATUS_SENT_TO_LECTURER,
        },
        {
            'title': 'Semester Postponement',
            'description': 'Semester to Postpone: Spring 2026\nReason Type: Medical\nExplanation: Need surgery and recovery time.',
            'request_type': Request.TYPE_POSTPONEMENT,
            'priority': Request.PRIORITY_HIGH,
            'status': Request.STATUS_SENT_TO_HOD,
        },
        {
            'title': 'Late Registration Request',
            'description': 'Category: Registration\nDescription: I missed the registration deadline due to technical issues with the system.',
            'request_type': Request.TYPE_GENERAL,
            'priority': Request.PRIORITY_MEDIUM,
            'status': Request.STATUS_IN_PROGRESS,
        },
        {
            'title': 'Previous Appeal - Approved',
            'description': 'Course Name: Algorithms\nGrade Received: 65\nExpected Grade: 75\nReason: Exam question was ambiguous.',
            'request_type': Request.TYPE_APPEAL,
            'priority': Request.PRIORITY_LOW,
            'status': Request.STATUS_APPROVED,
        },
    ]
    
    for req_data in requests_data:
        existing = Request.objects.filter(title=req_data['title'], student=student).first()
        if existing:
            print(f"  Exists: {req_data['title']}")
            continue
        
        request = Request.objects.create(
            student=student,
            title=req_data['title'],
            description=req_data['description'],
            request_type=req_data['request_type'],
            priority=req_data['priority'],
            status=req_data['status'],
        )
        
        # Create initial status history
        StatusHistory.objects.create(
            request=request,
            status=Request.STATUS_NEW,
            description="Request submitted by student.",
            role=StatusHistory.ROLE_STUDENT,
            changed_by=student,
        )
        
        # Add additional history for non-new requests
        if req_data['status'] != Request.STATUS_NEW:
            StatusHistory.objects.create(
                request=request,
                status=req_data['status'],
                description=f"Request status changed to {request.get_status_display()}.",
                role=StatusHistory.ROLE_STAFF,
            )
        
        # Create notification
        Notification.objects.create(
            user=student,
            request=request,
            message=f"Your request '{request.title}' has been submitted."
        )
        
        print(f"  Created: {req_data['title']} ({request.get_status_display()})")


def main():
    print("=" * 50)
    print("SCE Request Portal - Database Population Script")
    print("=" * 50)
    
    users = create_users()
    create_sample_requests(users)
    
    print("\n" + "=" * 50)
    print("DONE! Demo users created:")
    print("=" * 50)
    print("\nLogin credentials (all passwords follow the pattern shown):")
    print("-" * 50)
    print("Student:   student@ac.sce.ac.il  / Student1!")
    print("Staff:     staff@ac.sce.ac.il    / Staff123!")
    print("Lecturer:  lecturer@ac.sce.ac.il / Lecturer1!")
    print("HOD:       hod@ac.sce.ac.il      / Head1234!")
    print("-" * 50)
    print("\nRun the server with: python manage.py runserver")
    print("Access at: http://127.0.0.1:8000/auth/login/")
    print("=" * 50)


if __name__ == '__main__':
    main()
