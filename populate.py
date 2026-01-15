#!/usr/bin/env python
"""
Populate script - Creates demo data including degrees, courses, users, and sample requests.
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
from requests_unified.models import Request, StatusHistory, Notification, Degree, Course

User = get_user_model()


def create_degrees():
    """Create degree programs (departments)."""
    print("Creating degrees (departments)...")
    
    degrees_data = [
        {'name': 'Software Engineering', 'code': 'SE'},
        {'name': 'Computer Science', 'code': 'CS'},
        {'name': 'Electrical Engineering', 'code': 'EE'},
        {'name': 'Industrial Engineering', 'code': 'IE'},
        {'name': 'Civil Engineering', 'code': 'CE'},
    ]
    
    created_degrees = {}
    
    for degree_data in degrees_data:
        degree, created = Degree.objects.get_or_create(
            code=degree_data['code'],
            defaults={'name': degree_data['name'], 'is_active': True}
        )
        if created:
            print(f"  Created: {degree.name} ({degree.code})")
        else:
            print(f"  Exists: {degree.name} ({degree.code})")
        created_degrees[degree_data['code']] = degree
    
    return created_degrees


def create_courses(degrees):
    """Create courses and link them to degrees."""
    print("\nCreating courses...")
    
    courses_data = [
        # Software Engineering courses
        {'code': 'SE101', 'name': 'Introduction to Software Engineering', 'degrees': ['SE']},
        {'code': 'SE201', 'name': 'Software Design Patterns', 'degrees': ['SE', 'CS']},
        {'code': 'SE301', 'name': 'Software Project Management', 'degrees': ['SE']},
        {'code': 'SE401', 'name': 'Software Testing & QA', 'degrees': ['SE']},
        
        # Computer Science courses
        {'code': 'CS101', 'name': 'Introduction to Programming', 'degrees': ['CS', 'SE', 'EE']},
        {'code': 'CS201', 'name': 'Data Structures', 'degrees': ['CS', 'SE']},
        {'code': 'CS301', 'name': 'Algorithms', 'degrees': ['CS', 'SE']},
        {'code': 'CS401', 'name': 'Operating Systems', 'degrees': ['CS', 'SE']},
        {'code': 'CS402', 'name': 'Database Systems', 'degrees': ['CS', 'SE']},
        
        # Electrical Engineering courses
        {'code': 'EE101', 'name': 'Circuit Analysis', 'degrees': ['EE']},
        {'code': 'EE201', 'name': 'Digital Electronics', 'degrees': ['EE', 'CS']},
        {'code': 'EE301', 'name': 'Signal Processing', 'degrees': ['EE']},
        
        # General courses
        {'code': 'MATH101', 'name': 'Calculus I', 'degrees': ['SE', 'CS', 'EE', 'IE', 'CE']},
        {'code': 'MATH201', 'name': 'Linear Algebra', 'degrees': ['SE', 'CS', 'EE', 'IE', 'CE']},
        {'code': 'PHYS101', 'name': 'Physics I', 'degrees': ['SE', 'CS', 'EE', 'IE', 'CE']},
    ]
    
    created_courses = {}
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            code=course_data['code'],
            defaults={'name': course_data['name'], 'is_active': True}
        )
        
        # ALWAYS add degrees to course (even if course already exists)
        linked_degrees = []
        for degree_code in course_data['degrees']:
            if degree_code in degrees:
                course.degrees.add(degrees[degree_code])
                linked_degrees.append(degree_code)
        
        if created:
            print(f"  Created: {course.code} - {course.name} -> [{', '.join(linked_degrees)}]")
        else:
            print(f"  Exists: {course.code} - {course.name} -> Linked to: [{', '.join(linked_degrees)}]")
        
        created_courses[course_data['code']] = course
    
    return created_courses


def create_users(degrees, courses):
    """Create demo users for all roles with department assignments."""
    print("\nCreating demo users...")
    
    users_data = [
        # Students - each in a different degree
        {
            'username': 'student1',
            'email': 'student@ac.sce.ac.il',
            'password': 'Student1!',
            'first_name': 'Mahmood',
            'last_name': 'Gneam',
            'role': User.ROLE_STUDENT,
            'student_id': '123456789',
            'degree_code': 'SE',
        },
        {
            'username': 'student2',
            'email': 'student2@ac.sce.ac.il',
            'password': 'Student2!',
            'first_name': 'Sara',
            'last_name': 'Cohen',
            'role': User.ROLE_STUDENT,
            'student_id': '987654321',
            'degree_code': 'CS',
        },
        {
            'username': 'student3',
            'email': 'student3@ac.sce.ac.il',
            'password': 'Student3!',
            'first_name': 'David',
            'last_name': 'Levi',
            'role': User.ROLE_STUDENT,
            'student_id': '456789123',
            'degree_code': 'EE',
        },
        
        # Secretaries - each assigned to a department
        {
            'username': 'secretary_se',
            'email': 'secretary.se@ac.sce.ac.il',
            'password': 'Secretary1!',
            'first_name': 'Regena',
            'last_name': 'Regena',
            'role': User.ROLE_SECRETARY,
            'degree_code': 'SE',  # Software Engineering secretary
        },
        {
            'username': 'secretary_cs',
            'email': 'secretary.cs@ac.sce.ac.il',
            'password': 'Secretary2!',
            'first_name': 'Rachel',
            'last_name': 'Green',
            'role': User.ROLE_SECRETARY,
            'degree_code': 'CS',  # Computer Science secretary
        },
        {
            'username': 'secretary_ee',
            'email': 'secretary.ee@ac.sce.ac.il',
            'password': 'Secretary3!',
            'first_name': 'Monica',
            'last_name': 'Geller',
            'role': User.ROLE_SECRETARY,
            'degree_code': 'EE',  # Electrical Engineering secretary
        },
        
        # Lecturers - each assigned to a department and courses
        {
            'username': 'lecturer_se',
            'email': 'lecturer.se@ac.sce.ac.il',
            'password': 'Lecturer1!',
            'first_name': 'Dr. Michael',
            'last_name': 'Ross',
            'role': User.ROLE_LECTURER,
            'degree_code': 'SE',
            'courses': ['SE101', 'SE201', 'SE301'],
        },
        {
            'username': 'lecturer_cs',
            'email': 'lecturer.cs@ac.sce.ac.il',
            'password': 'Lecturer2!',
            'first_name': 'Dr. Emily',
            'last_name': 'Chen',
            'role': User.ROLE_LECTURER,
            'degree_code': 'CS',
            'courses': ['CS101', 'CS201', 'CS301', 'CS401'],
        },
        {
            'username': 'lecturer_ee',
            'email': 'lecturer.ee@ac.sce.ac.il',
            'password': 'Lecturer3!',
            'first_name': 'Dr. James',
            'last_name': 'Wilson',
            'role': User.ROLE_LECTURER,
            'degree_code': 'EE',
            'courses': ['EE101', 'EE201', 'EE301'],
        },
        {
            'username': 'lecturer_math',
            'email': 'lecturer.math@ac.sce.ac.il',
            'password': 'Lecturer4!',
            'first_name': 'Dr. Anna',
            'last_name': 'Katz',
            'role': User.ROLE_LECTURER,
            'degree_code': 'SE',  # Primary department
            'courses': ['MATH101', 'MATH201'],
        },
        
        # Head of Department
        {
            'username': 'hod1',
            'email': 'hod@ac.sce.ac.il',
            'password': 'Head1234!',
            'first_name': 'Prof. David',
            'last_name': 'Department Head',
            'role': User.ROLE_HEAD_OF_DEPT,
            'degree_code': 'SE',
        },
        
        # Admin
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
        # Get degree if specified
        degree = None
        if 'degree_code' in user_data and user_data['degree_code'] in degrees:
            degree = degrees[user_data['degree_code']]
        
        # Build defaults
        defaults = {
            'username': user_data['username'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'role': user_data['role'],
        }
        
        if degree:
            defaults['degree'] = degree
        
        if 'student_id' in user_data:
            defaults['student_id'] = user_data['student_id']
        
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults=defaults
        )
        
        if created:
            user.set_password(user_data['password'])
            if degree:
                user.degree = degree
            user.save()
            print(f"  Created: {user.email} ({user.get_role_display()}) - Dept: {degree.code if degree else 'N/A'}")
        else:
            # Update degree if not set
            if degree and not user.degree:
                user.degree = degree
                user.save()
            print(f"  Exists: {user.email} ({user.get_role_display()}) - Dept: {user.degree.code if user.degree else 'N/A'}")
        
        # Assign courses to lecturers
        if user_data['role'] == User.ROLE_LECTURER and 'courses' in user_data:
            for course_code in user_data['courses']:
                if course_code in courses:
                    course = courses[course_code]
                    course.lecturers.add(user)
                    print(f"    -> Assigned to course: {course_code}")
        
        created_users[user_data['email']] = user
    
    return created_users


def create_sample_requests(users, degrees, courses):
    """Create sample requests in various statuses."""
    print("\nCreating sample requests...")
    
    # Get a student
    student = users.get('student@ac.sce.ac.il')
    if not student:
        print("  No student found, skipping requests")
        return
    
    # Get lecturer and secretary
    lecturer = users.get('lecturer.se@ac.sce.ac.il')
    
    # Get a course
    course = courses.get('SE201')
    
    requests_data = [
        {
            'title': 'Course Overload Request',
            'description': 'I would like to take 6 courses this semester to complete my degree requirements on time.',
            'request_type': Request.TYPE_STUDY_APPROVAL,
            'priority': Request.PRIORITY_HIGH,
            'status': Request.STATUS_NEW,
            'course': course,
        },
        {
            'title': 'Grade Appeal - Data Structures',
            'description': 'Course Name: Data Structures\nGrade Received: 72\nExpected Grade: 85\nReason: I believe my final exam was graded incorrectly.',
            'request_type': Request.TYPE_APPEAL,
            'priority': Request.PRIORITY_MEDIUM,
            'status': Request.STATUS_SENT_TO_LECTURER,
            'course': courses.get('CS201'),
            'assigned_lecturer': lecturer,
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
            'course': courses.get('CS301'),
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
            course=req_data.get('course'),
            assigned_lecturer=req_data.get('assigned_lecturer'),
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
    print("=" * 60)
    print("SCE Request Portal - Database Population Script")
    print("=" * 60)
    
    # Create data in order
    degrees = create_degrees()
    courses = create_courses(degrees)
    users = create_users(degrees, courses)
    create_sample_requests(users, degrees, courses)
    
    print("\n" + "=" * 60)
    print("DONE! Sample data created successfully!")
    print("=" * 60)
    
    print("\n📚 DEGREES CREATED:")
    print("-" * 40)
    for code, degree in degrees.items():
        print(f"  {code}: {degree.name}")
    
    print("\n👥 LOGIN CREDENTIALS:")
    print("-" * 40)
    print("STUDENTS:")
    print("  student@ac.sce.ac.il      / Student1!    (SE Dept)")
    print("  student2@ac.sce.ac.il     / Student2!    (CS Dept)")
    print("  student3@ac.sce.ac.il     / Student3!    (EE Dept)")
    print("\nSECRETARIES:")
    print("  secretary.se@ac.sce.ac.il / Secretary1!  (SE Dept)")
    print("  secretary.cs@ac.sce.ac.il / Secretary2!  (CS Dept)")
    print("  secretary.ee@ac.sce.ac.il / Secretary3!  (EE Dept)")
    print("\nLECTURERS:")
    print("  lecturer.se@ac.sce.ac.il  / Lecturer1!   (SE Dept)")
    print("  lecturer.cs@ac.sce.ac.il  / Lecturer2!   (CS Dept)")
    print("  lecturer.ee@ac.sce.ac.il  / Lecturer3!   (EE Dept)")
    print("\nHOD & ADMIN:")
    print("  hod@ac.sce.ac.il          / Head1234!")
    print("  admin@ac.sce.ac.il        / Admin123!")
    print("-" * 40)
    print("\nRun the server with: python manage.py runserver")
    print("=" * 60)


if __name__ == '__main__':
    main()
