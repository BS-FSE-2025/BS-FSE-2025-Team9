"""
Tests for full request workflow: submit -> review -> approve/reject.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request, StatusHistory


class FullRequestWorkflowTest(TestCase):
    """Tests for complete request workflow."""
    
    def setUp(self):
        self.client = Client()
        
        # Create degree and course
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        # Create users
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789",
            degree=self.degree
        )
        
        self.secretary = User.objects.create_user(
            username="secretary",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Dept"
        )
    
    def test_full_approval_workflow(self):
        """Test: Student submits -> Secretary reviews -> Lecturer approves."""
        # Step 1: Student submits request
        self.client.force_login(self.student)
        
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Study Approval',
            'title': 'Need approval for SE101',
            'priority': 'medium',
            'course': self.course.id,
            'semester': 'Spring 2026',
            'reason': 'I need this course for my degree',
        })
        
        self.assertEqual(response.status_code, 302)
        request = Request.objects.get(student=self.student)
        self.assertEqual(request.status, Request.STATUS_NEW)
        
        # Step 2: Secretary forwards to lecturer
        self.client.force_login(self.secretary)
        
        response = self.client.post(
            reverse('staff:send_to_lecturer', args=[request.id]),
            {'lecturer_id': self.lecturer.id}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_SENT_TO_LECTURER)
        self.assertEqual(request.assigned_lecturer, self.lecturer)
        
        # Step 3: Lecturer approves
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:approve', args=[request.id]),
            {'feedback': 'Approved - meets requirements'}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_APPROVED)
        
        # Step 4: Student sees approved request
        self.client.force_login(self.student)
        
        response = self.client.get(
            reverse('students:request_detail', args=[request.request_id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved")
    
    def test_rejection_workflow(self):
        """Test: Student submits -> Lecturer rejects."""
        # Create request
        request = Request.objects.create(
            student=self.student,
            title="Appeal Request",
            description="Grade appeal",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER,
            assigned_lecturer=self.lecturer
        )
        
        # Lecturer rejects
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:reject', args=[request.id]),
            {'feedback': 'Does not meet criteria'}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_REJECTED)
    
    def test_escalation_to_hod_workflow(self):
        """Test: Student submits -> Secretary -> Lecturer -> HOD."""
        request = Request.objects.create(
            student=self.student,
            title="Complex Request",
            description="Needs HOD review",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER,
            assigned_lecturer=self.lecturer
        )
        
        # Lecturer forwards to HOD
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:forward_to_hod', args=[request.id]),
            {'feedback': 'Need HOD decision on this'}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_SENT_TO_HOD)
        
        # HOD approves
        self.client.force_login(self.hod)
        
        response = self.client.post(
            reverse('head_of_dept:approve', args=[request.id]),
            {'notes': 'Approved by department head'}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_APPROVED)
    
    def test_needs_info_workflow(self):
        """Test: Lecturer requests more info -> Student updates."""
        request = Request.objects.create(
            student=self.student,
            title="Incomplete Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER,
            assigned_lecturer=self.lecturer
        )
        
        # Lecturer requests more info
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:needs_info', args=[request.id]),
            {'feedback': 'Please provide more details'}
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_NEEDS_INFO)
        
        # Student sees request needs more info
        self.client.force_login(self.student)
        
        response = self.client.get(
            reverse('students:request_detail', args=[request.request_id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "more details")


class RequestStatusHistoryTest(TestCase):
    """Tests for request status history tracking."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789",
            degree=self.degree
        )
        
        self.secretary = User.objects.create_user(
            username="secretary",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
    
    def test_status_history_created_on_status_change(self):
        """Test that status history entries are created on changes."""
        request = Request.objects.create(
            student=self.student,
            title="Test Request",
            description="Description",
            status=Request.STATUS_NEW
        )
        
        initial_count = StatusHistory.objects.filter(request=request).count()
        
        # Secretary changes status
        self.client.force_login(self.secretary)
        
        response = self.client.post(
            reverse('staff:send_to_hod', args=[request.id])
        )
        
        new_count = StatusHistory.objects.filter(request=request).count()
        self.assertEqual(new_count, initial_count + 1)
        
        last_history = StatusHistory.objects.filter(request=request).latest('created_at')
        self.assertEqual(last_history.status, Request.STATUS_SENT_TO_HOD)


class DirectToHODWorkflowTest(TestCase):
    """Tests for requests that go directly to HOD."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789",
            degree=self.degree
        )
        
        self.secretary = User.objects.create_user(
            username="secretary",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
    
    def test_request_without_course_goes_to_hod(self):
        """Test requests without course can only go to HOD."""
        request = Request.objects.create(
            student=self.student,
            title="Postponement Request",
            description="Need to postpone",
            request_type=Request.TYPE_POSTPONEMENT,
            course=None,  # No course
            status=Request.STATUS_NEW
        )
        
        self.client.force_login(self.secretary)
        
        # Should only be able to send to HOD
        response = self.client.post(
            reverse('staff:send_to_hod', args=[request.id])
        )
        
        self.assertEqual(response.status_code, 302)
        request.refresh_from_db()
        self.assertEqual(request.status, Request.STATUS_SENT_TO_HOD)
