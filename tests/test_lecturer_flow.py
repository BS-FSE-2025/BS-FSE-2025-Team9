"""
Tests for lecturer flows: dashboard filtering, approve/reject.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request


class LecturerDashboardFilterTest(TestCase):
    """Tests for lecturer dashboard filtering by courses."""
    
    def setUp(self):
        self.client = Client()
        
        # Create degrees and courses
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.course1 = Course.objects.create(code="SE101", name="Course 1")
        self.course1.degrees.add(self.degree)
        
        self.course2 = Course.objects.create(code="SE102", name="Course 2")
        self.course2.degrees.add(self.degree)
        
        # Create lecturers
        self.lecturer1 = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        
        self.lecturer2 = User.objects.create_user(
            username="lecturer2",
            email="lecturer2@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="Jane",
            last_name="Professor"
        )
        
        # Assign lecturer1 to course1 only
        self.course1.lecturers.add(self.lecturer1)
        # Assign lecturer2 to course2 only
        self.course2.lecturers.add(self.lecturer2)
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789",
            degree=self.degree
        )
        
        # Create requests for different courses
        self.request_course1 = Request.objects.create(
            student=self.student,
            title="Request for Course 1",
            description="Description",
            course=self.course1,
            status=Request.STATUS_SENT_TO_LECTURER
        )
        
        self.request_course2 = Request.objects.create(
            student=self.student,
            title="Request for Course 2",
            description="Description",
            course=self.course2,
            status=Request.STATUS_SENT_TO_LECTURER
        )
    
    def test_lecturer_sees_only_their_courses(self):
        """Test that lecturer only sees requests for courses they teach."""
        self.client.force_login(self.lecturer1)
        
        response = self.client.get(reverse('lecturers:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request for Course 1")
        self.assertNotContains(response, "Request for Course 2")
    
    def test_lecturer_sees_explicitly_assigned_requests(self):
        """Test that lecturer sees requests explicitly assigned to them."""
        # Explicitly assign request_course2 to lecturer1 (even though not in their courses)
        self.request_course2.assigned_lecturer = self.lecturer1
        self.request_course2.save()
        
        self.client.force_login(self.lecturer1)
        
        response = self.client.get(reverse('lecturers:dashboard'))
        
        # Should now see both requests
        self.assertContains(response, "Request for Course 1")
        self.assertContains(response, "Request for Course 2")


class LecturerApprovalTest(TestCase):
    """Tests for lecturer approval/rejection flow."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789",
            degree=self.degree
        )
        
        self.request = Request.objects.create(
            student=self.student,
            title="Test Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER
        )
        
        self.client.force_login(self.lecturer)
    
    def test_approve_request(self):
        """Test approving a request."""
        response = self.client.post(
            reverse('lecturers:approve', args=[self.request.id]),
            {'feedback': 'Approved - looks good'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_APPROVED)
        self.assertEqual(self.request.assigned_lecturer, self.lecturer)
        self.assertEqual(self.request.lecturer_feedback, 'Approved - looks good')
    
    def test_reject_request_requires_reason(self):
        """Test that rejection requires a reason."""
        response = self.client.post(
            reverse('lecturers:reject', args=[self.request.id]),
            {'feedback': ''}  # Empty feedback
        )
        
        self.request.refresh_from_db()
        # Should still be in SENT_TO_LECTURER status
        self.assertEqual(self.request.status, Request.STATUS_SENT_TO_LECTURER)
    
    def test_reject_request_with_reason(self):
        """Test rejecting a request with a reason."""
        response = self.client.post(
            reverse('lecturers:reject', args=[self.request.id]),
            {'feedback': 'Does not meet requirements'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_REJECTED)
        self.assertIn('Does not meet requirements', self.request.lecturer_feedback)
    
    def test_forward_to_hod(self):
        """Test forwarding a request to HOD."""
        response = self.client.post(
            reverse('lecturers:forward_to_hod', args=[self.request.id]),
            {'feedback': 'Needs HOD review'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_SENT_TO_HOD)
    
    def test_needs_info(self):
        """Test marking request as needing more info."""
        response = self.client.post(
            reverse('lecturers:needs_info', args=[self.request.id]),
            {'feedback': 'Please provide more details'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_NEEDS_INFO)
