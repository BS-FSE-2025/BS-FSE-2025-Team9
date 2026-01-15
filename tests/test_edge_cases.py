"""
Tests for edge cases and boundary conditions.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request


class EmptyDataTest(TestCase):
    """Tests for handling empty/no data scenarios."""
    
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
    
    def test_student_dashboard_with_no_requests(self):
        """Test student dashboard displays correctly with no requests."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('students:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_staff_dashboard_with_no_requests(self):
        """Test staff dashboard displays correctly with no requests."""
        self.client.force_login(self.secretary)
        
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_request_form_with_no_courses(self):
        """Test request form works when no courses exist for degree."""
        # Remove all courses from degree
        Course.objects.filter(degrees=self.degree).delete()
        
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('students:submit_request'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_degree_list_empty(self):
        """Test degree list when no degrees exist."""
        Degree.objects.all().delete()
        
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        self.client.force_login(admin)
        
        response = self.client.get(reverse('management:degree_list'))
        
        self.assertEqual(response.status_code, 200)


class CourseWithNoLecturersTest(TestCase):
    """Tests for courses that have no lecturers assigned."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        # Note: No lecturers assigned
        
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
    
    def test_secretary_sees_no_lecturers_available(self):
        """Test secretary sees no lecturers for course without lecturers."""
        request = Request.objects.create(
            student=self.student,
            title="Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_NEW
        )
        
        self.client.force_login(self.secretary)
        
        response = self.client.get(
            reverse('staff:request_detail', args=[request.id])
        )
        
        self.assertEqual(response.status_code, 200)
        # Should show option to send to HOD since no lecturers


class InactiveCoursesDegreeTest(TestCase):
    """Tests for inactive courses and degrees."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        # Create active and inactive courses
        self.active_course = Course.objects.create(
            code="SE101", 
            name="Active Course", 
            is_active=True
        )
        self.active_course.degrees.add(self.degree)
        
        self.inactive_course = Course.objects.create(
            code="SE102", 
            name="Inactive Course", 
            is_active=False
        )
        self.inactive_course.degrees.add(self.degree)
        
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
    
    def test_inactive_courses_hidden_in_request_form(self):
        """Test that inactive courses are not shown in request form."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('students:submit_request'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active Course")
        self.assertNotContains(response, "Inactive Course")


class ConcurrentRequestsTest(TestCase):
    """Tests for handling multiple requests for same student/course."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
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
    
    def test_student_can_have_multiple_pending_requests(self):
        """Test student can have multiple pending requests."""
        self.client.force_login(self.student)
        
        # Submit first request
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Study Approval',
            'title': 'Request 1',
            'priority': 'medium',
            'course': self.course.id,
            'semester': 'Spring 2026',
            'reason': 'Reason 1',
        })
        self.assertEqual(response.status_code, 302)
        
        # Submit second request
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Appeal',
            'title': 'Request 2',
            'priority': 'high',
            'course': self.course.id,
            'appeal_reason': 'Reason 2',
            'original_grade': 'B',
            'expected_grade': 'A',
        })
        self.assertEqual(response.status_code, 302)
        
        # Both should exist
        self.assertEqual(Request.objects.filter(student=self.student).count(), 2)


class SpecialCharactersTest(TestCase):
    """Tests for handling special characters in inputs."""
    
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
    
    def test_request_with_hebrew_text(self):
        """Test request with Hebrew characters in title/description."""
        self.client.force_login(self.student)
        
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Postponement',
            'title': 'בקשה לדחייה',  # Hebrew title
            'priority': 'medium',
            'semester': 'אביב 2026',  # Hebrew semester
            'reason_type': 'Personal',
            'explanation': 'סיבה אישית',  # Hebrew explanation
        })
        
        self.assertEqual(response.status_code, 302)
        
        request = Request.objects.get(student=self.student)
        self.assertIn('בקשה', request.title)
    
    def test_course_name_with_special_chars(self):
        """Test course with special characters in name."""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        self.client.force_login(admin)
        
        response = self.client.post(reverse('management:course_add'), {
            'name': 'C++ Programming & Design',
            'code': 'CS201',
            'degrees': [self.degree.id],
            'is_active': 'on',
        })
        
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(code='CS201')
        self.assertIn('C++', course.name)


class LargeDataTest(TestCase):
    """Tests for handling larger amounts of data."""
    
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
    
    def test_dashboard_with_many_requests(self):
        """Test dashboard performance with many requests."""
        # Create 50 requests
        for i in range(50):
            Request.objects.create(
                student=self.student,
                title=f"Request {i}",
                description=f"Description {i}",
                status=Request.STATUS_NEW
            )
        
        self.client.force_login(self.secretary)
        
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_long_description(self):
        """Test request with very long description."""
        self.client.force_login(self.student)
        
        long_text = "A" * 5000  # 5000 character description
        
        response = self.client.post(reverse('students:submit_request'), {
            'request_type': 'Postponement',
            'title': 'Long request',
            'priority': 'medium',
            'semester': 'Spring 2026',
            'reason_type': 'Personal',
            'explanation': long_text,
        })
        
        self.assertEqual(response.status_code, 302)
        
        request = Request.objects.get(student=self.student)
        # Description includes form labels + the long text
        self.assertIn(long_text, request.description)
        self.assertGreater(len(request.description), 5000)


class InvalidRequestIDTest(TestCase):
    """Tests for invalid request IDs."""
    
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
    
    def test_nonexistent_request_id(self):
        """Test accessing nonexistent request returns 404."""
        self.client.force_login(self.student)
        
        response = self.client.get(
            reverse('students:request_detail', args=['REQ-NONEXISTENT'])
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_malformed_request_id(self):
        """Test accessing malformed request ID."""
        self.client.force_login(self.student)
        
        response = self.client.get(
            reverse('students:request_detail', args=['invalid-format'])
        )
        
        self.assertEqual(response.status_code, 404)
