"""
Tests for HOD flows: view all requests, override lecturer decisions.
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest import skip

from core.models import User
from requests_unified.models import Degree, Course, Request


class HODDashboardTest(TestCase):
    """Tests for HOD dashboard."""
    
    def setUp(self):
        self.client = Client()
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Department"
        )
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
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
        
        # Create requests with different statuses
        self.request_to_hod = Request.objects.create(
            student=self.student,
            title="Request sent to HOD",
            description="Description",
            status=Request.STATUS_SENT_TO_HOD
        )
        
        self.request_approved = Request.objects.create(
            student=self.student,
            title="Approved request",
            description="Description",
            status=Request.STATUS_APPROVED
        )
        
        self.client.force_login(self.hod)
    
    def test_hod_sees_requests_sent_to_them(self):
        """Test that HOD sees requests sent to them."""
        response = self.client.get(reverse('head_of_dept:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request sent to HOD")
    
    @skip("all_requests endpoint not yet implemented")
    def test_hod_can_view_all_requests(self):
        """Test that HOD can see all requests in history view."""
        response = self.client.get(reverse('head_of_dept:all_requests'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request sent to HOD")
        self.assertContains(response, "Approved request")


class HODOverrideDecisionTest(TestCase):
    """Tests for HOD overriding lecturer decisions."""
    
    def setUp(self):
        self.client = Client()
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Department"
        )
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
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
        
        # Create a rejected request
        self.rejected_request = Request.objects.create(
            student=self.student,
            title="Rejected Request",
            description="Description",
            course=self.course,
            assigned_lecturer=self.lecturer,
            lecturer_feedback="Rejected by lecturer",
            status=Request.STATUS_REJECTED
        )
        
        self.client.force_login(self.hod)
    
    @skip("override_decision endpoint not yet implemented")
    def test_hod_can_override_rejection(self):
        """Test that HOD can override a lecturer's rejection."""
        response = self.client.post(
            reverse('head_of_dept:override_decision', args=[self.rejected_request.id]),
            {
                'new_status': 'approved',
                'override_reason': 'Overriding - student has valid reasons'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.rejected_request.refresh_from_db()
        self.assertEqual(self.rejected_request.status, Request.STATUS_APPROVED)
        self.assertIn("Overriding", self.rejected_request.hod_feedback)
    
    @skip("override_decision endpoint not yet implemented")
    def test_hod_can_override_approval(self):
        """Test that HOD can override a lecturer's approval."""
        self.rejected_request.status = Request.STATUS_APPROVED
        self.rejected_request.save()
        
        response = self.client.post(
            reverse('head_of_dept:override_decision', args=[self.rejected_request.id]),
            {
                'new_status': 'rejected',
                'override_reason': 'Overriding - policy violation'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.rejected_request.refresh_from_db()
        self.assertEqual(self.rejected_request.status, Request.STATUS_REJECTED)


class HODApprovalTest(TestCase):
    """Tests for HOD direct approval/rejection."""
    
    def setUp(self):
        self.client = Client()
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Department"
        )
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
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
            title="Request to HOD",
            description="Description",
            status=Request.STATUS_SENT_TO_HOD
        )
        
        self.client.force_login(self.hod)
    
    def test_hod_direct_approval(self):
        """Test HOD can directly approve a request."""
        response = self.client.post(
            reverse('head_of_dept:approve', args=[self.request.id]),
            {'notes': 'Approved by HOD'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_APPROVED)
    
    def test_hod_direct_rejection(self):
        """Test HOD can directly reject a request."""
        response = self.client.post(
            reverse('head_of_dept:reject', args=[self.request.id]),
            {'notes': 'Rejected - does not meet criteria'}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_REJECTED)
    
    @skip("send_to_lecturer endpoint not yet implemented")
    def test_hod_can_send_back_to_lecturer(self):
        """Test HOD can send a request back to a lecturer."""
        course = Course.objects.create(code="SE101", name="Course 1")
        course.degrees.add(self.degree)
        
        lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        course.lecturers.add(lecturer)
        
        self.request.course = course
        self.request.save()
        
        response = self.client.post(
            reverse('head_of_dept:send_to_lecturer', args=[self.request.id]),
            {
                'lecturer_id': lecturer.id,
                'feedback': 'Please review this request'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_SENT_TO_LECTURER)
        self.assertEqual(self.request.assigned_lecturer, lecturer)
