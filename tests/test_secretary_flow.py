"""
Tests for secretary flows: forward to lecturer with course filtering.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request, StatusHistory


class SecretaryForwardToLecturerTest(TestCase):
    """Tests for secretary forwarding requests to lecturers."""
    
    def setUp(self):
        self.client = Client()
        
        # Create degree and course
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Software Eng Basics")
        self.course.degrees.add(self.degree)
        
        # Create users
        self.secretary = User.objects.create_user(
            username="secretary1",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
        
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
        
        # Assign only lecturer1 to the course
        self.course.lecturers.add(self.lecturer1)
        
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
        
        # Create a request with course
        self.request_with_course = Request.objects.create(
            student=self.student,
            title="Study Approval",
            description="Need approval",
            request_type=Request.TYPE_STUDY_APPROVAL,
            course=self.course,
            status=Request.STATUS_NEW
        )
        
        # Create a request without course
        self.request_without_course = Request.objects.create(
            student=self.student,
            title="Postponement",
            description="Need postponement",
            request_type=Request.TYPE_POSTPONEMENT,
            course=None,
            status=Request.STATUS_NEW
        )
        
        self.client.force_login(self.secretary)
    
    def test_request_detail_shows_available_lecturers(self):
        """Test that request detail shows lecturers for the course."""
        response = self.client.get(
            reverse('staff:request_detail', args=[self.request_with_course.id])
        )
        
        self.assertEqual(response.status_code, 200)
        # Should show lecturer1 who is assigned to the course
        self.assertContains(response, "John Lecturer")
        # Should NOT show lecturer2 who is not assigned
        self.assertNotContains(response, "Jane Professor")
    
    def test_forward_to_lecturer_with_course(self):
        """Test forwarding a request to a specific lecturer."""
        response = self.client.post(
            reverse('staff:send_to_lecturer', args=[self.request_with_course.id]),
            {'lecturer_id': self.lecturer1.id}
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request_with_course.refresh_from_db()
        self.assertEqual(self.request_with_course.status, Request.STATUS_SENT_TO_LECTURER)
        self.assertEqual(self.request_with_course.assigned_lecturer, self.lecturer1)
    
    def test_cannot_forward_to_unassigned_lecturer(self):
        """Test that cannot forward to a lecturer not assigned to the course."""
        response = self.client.post(
            reverse('staff:send_to_lecturer', args=[self.request_with_course.id]),
            {'lecturer_id': self.lecturer2.id}  # Not assigned to the course
        )
        
        self.request_with_course.refresh_from_db()
        # Should still be NEW status
        self.assertEqual(self.request_with_course.status, Request.STATUS_NEW)
    
    def test_cannot_forward_request_without_course(self):
        """Test that requests without course cannot be forwarded to lecturer."""
        response = self.client.post(
            reverse('staff:send_to_lecturer', args=[self.request_without_course.id]),
            {'lecturer_id': self.lecturer1.id}
        )
        
        self.request_without_course.refresh_from_db()
        # Should still be NEW status
        self.assertEqual(self.request_without_course.status, Request.STATUS_NEW)
    
    def test_forward_to_hod_always_available(self):
        """Test that forwarding to HOD is always available."""
        response = self.client.post(
            reverse('staff:send_to_hod', args=[self.request_without_course.id])
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.request_without_course.refresh_from_db()
        self.assertEqual(self.request_without_course.status, Request.STATUS_SENT_TO_HOD)


class SecretaryDashboardTest(TestCase):
    """Tests for secretary dashboard."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.secretary = User.objects.create_user(
            username="secretary1",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
        
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
        
        # Create requests
        self.request_new = Request.objects.create(
            student=self.student,
            title="New Request",
            description="Description",
            status=Request.STATUS_NEW
        )
        
        self.request_approved = Request.objects.create(
            student=self.student,
            title="Approved Request",
            description="Description",
            status=Request.STATUS_APPROVED
        )
        
        self.client.force_login(self.secretary)
    
    def test_dashboard_shows_active_requests(self):
        """Test that dashboard shows active (non-completed) requests."""
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Request")
        # Approved requests should be filtered out by default
    
    def test_add_note_updates_status(self):
        """Test that adding a note changes status to in_progress."""
        response = self.client.post(
            reverse('staff:add_note', args=[self.request_new.id]),
            {'text': 'Reviewing this request'}
        )
        
        self.request_new.refresh_from_db()
        self.assertEqual(self.request_new.status, Request.STATUS_IN_PROGRESS)
