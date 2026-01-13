"""
Tests for student flows: signup, submit requests, view dashboard.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request


class StudentSignupTest(TestCase):
    """Tests for student registration with degree."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
    
    def test_signup_page_shows_degrees(self):
        """Test that signup page displays available degrees."""
        response = self.client.get(reverse('core:signup'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SE - Software Engineering")
    
    def test_signup_with_degree(self):
        """Test successful signup with degree selection."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        # Should redirect to login on success
        self.assertEqual(response.status_code, 302)
        
        # Check user was created with degree
        user = User.objects.get(email='john.doe@sce.ac.il')
        self.assertEqual(user.degree, self.degree)
        self.assertEqual(user.student_id, '123456789')
    
    def test_signup_invalid_student_id(self):
        """Test signup fails with invalid student ID."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '12345',  # Only 5 digits
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.assertContains(response, "9 digits")
    
    def test_signup_invalid_email_domain(self):
        """Test signup fails with non-SCE email."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@gmail.com',  # Invalid domain
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sce.ac.il")
    
    def test_signup_requires_degree(self):
        """Test signup fails without degree selection."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '123456789',
            # No degree selected
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.assertContains(response, "degree")
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())


class StudentRequestFormTest(TestCase):
    """Tests for student request submission with courses."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.other_degree = Degree.objects.create(name="Computer Science", code="CS")
        
        self.course = Course.objects.create(code="SE101", name="Software Eng Basics")
        self.course.degrees.add(self.degree)
        
        self.other_course = Course.objects.create(code="CS101", name="CS Basics")
        self.other_course.degrees.add(self.other_degree)
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Jane",
            last_name="Student",
            student_id="123456789",
            degree=self.degree
        )
        self.client.force_login(self.student)
    
    def test_request_form_shows_degree_courses(self):
        """Test that request form only shows courses from student's degree."""
        response = self.client.get(reverse('students:submit_request'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SE101 - Software Eng Basics")
        self.assertNotContains(response, "CS101 - CS Basics")
    
    def test_submit_study_approval_request(self):
        """Test submitting a study approval request with course."""
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Study Approval',
            'title': 'Study Approval for SE101',
            'priority': 'medium',
            'course': self.course.id,
            'semester': 'Spring 2026',
            'reason': 'I need this course for my degree',
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        
        request = Request.objects.get(student=self.student)
        self.assertEqual(request.course, self.course)
        self.assertEqual(request.request_type, 'Study Approval')
    
    def test_submit_postponement_no_course(self):
        """Test submitting a postponement request (no course needed)."""
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Postponement',
            'title': 'Postponement Request',
            'priority': 'high',
            'semester': 'Fall 2026',
            'reason_type': 'Medical',
            'explanation': 'Medical reasons',
        })
        
        self.assertEqual(response.status_code, 302)
        
        request = Request.objects.get(student=self.student)
        self.assertIsNone(request.course)
        self.assertEqual(request.request_type, 'Postponement')


class StudentDashboardTest(TestCase):
    """Tests for student dashboard."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Jane",
            last_name="Student",
            student_id="123456789",
            degree=self.degree
        )
        self.client.force_login(self.student)
        
        # Create some requests
        self.request1 = Request.objects.create(
            student=self.student,
            title="Test Request 1",
            description="Description 1",
            status=Request.STATUS_NEW
        )
        self.request2 = Request.objects.create(
            student=self.student,
            title="Test Request 2",
            description="Description 2",
            status=Request.STATUS_APPROVED
        )
    
    def test_dashboard_shows_requests(self):
        """Test that dashboard shows student's requests."""
        response = self.client.get(reverse('students:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Request 1")
        self.assertContains(response, "Test Request 2")
    
    def test_dashboard_filter_by_status(self):
        """Test filtering requests by status."""
        response = self.client.get(reverse('students:dashboard') + '?status=approved')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Request 2")
    
    def test_request_detail_uses_request_id(self):
        """Test that request detail uses request_id in URL."""
        response = self.client.get(
            reverse('students:request_detail', args=[self.request1.request_id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Request 1")
