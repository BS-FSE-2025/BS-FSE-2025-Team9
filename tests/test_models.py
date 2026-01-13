"""
Tests for models: Degree, Course, Request, User relationships.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from core.models import User
from requests_unified.models import Degree, Course, Request


class DegreeModelTest(TestCase):
    """Tests for the Degree model."""
    
    def test_create_degree(self):
        """Test creating a degree."""
        degree = Degree.objects.create(
            name="Software Engineering",
            code="SE"
        )
        self.assertEqual(str(degree), "SE - Software Engineering")
        self.assertTrue(degree.is_active)
    
    def test_degree_code_unique(self):
        """Test that degree codes must be unique."""
        Degree.objects.create(name="Software Engineering", code="SE")
        with self.assertRaises(Exception):
            Degree.objects.create(name="Systems Engineering", code="SE")


class CourseModelTest(TestCase):
    """Tests for the Course model."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Doe"
        )
    
    def test_create_course(self):
        """Test creating a course."""
        course = Course.objects.create(
            code="CS101",
            name="Introduction to Programming"
        )
        course.degrees.add(self.degree)
        
        self.assertEqual(str(course), "CS101 - Introduction to Programming")
        self.assertTrue(course.is_active)
        self.assertIn(self.degree, course.degrees.all())
    
    def test_course_with_lecturer(self):
        """Test assigning a lecturer to a course."""
        course = Course.objects.create(
            code="CS101",
            name="Introduction to Programming"
        )
        course.degrees.add(self.degree)
        course.lecturers.add(self.lecturer)
        
        self.assertIn(self.lecturer, course.lecturers.all())
        self.assertIn(course, self.lecturer.taught_courses.all())
    
    def test_course_code_unique(self):
        """Test that course codes must be unique."""
        Course.objects.create(code="CS101", name="Intro to CS")
        with self.assertRaises(Exception):
            Course.objects.create(code="CS101", name="Another CS Course")


class UserModelTest(TestCase):
    """Tests for the User model with degree relation."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
    
    def test_create_student_with_degree(self):
        """Test creating a student with a degree."""
        student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Jane",
            last_name="Student",
            student_id="123456789",
            degree=self.degree
        )
        
        self.assertEqual(student.degree, self.degree)
        self.assertIn(student, self.degree.students.all())
    
    def test_admin_role_auto_set_for_superuser(self):
        """Test that superusers get admin role automatically."""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        self.assertEqual(admin.role, User.ROLE_ADMIN)
        self.assertTrue(admin.is_admin)


class RequestWithCourseTest(TestCase):
    """Tests for Request model with course relation."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="CS101", name="Intro to CS")
        self.course.degrees.add(self.degree)
        
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
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
    
    def test_create_request_with_course(self):
        """Test creating a request with a course."""
        request = Request.objects.create(
            student=self.student,
            title="Study Approval Request",
            description="I need approval for this course",
            request_type=Request.TYPE_STUDY_APPROVAL,
            course=self.course
        )
        
        self.assertEqual(request.course, self.course)
        self.assertIn(request, self.course.requests.all())
        self.assertTrue(request.request_id.startswith("REQ-"))
    
    def test_request_without_course(self):
        """Test creating a request without a course (postponement)."""
        request = Request.objects.create(
            student=self.student,
            title="Postponement Request",
            description="I need to postpone my studies",
            request_type=Request.TYPE_POSTPONEMENT,
            course=None
        )
        
        self.assertIsNone(request.course)
    
    def test_request_assigned_lecturer(self):
        """Test assigning a lecturer to a request."""
        request = Request.objects.create(
            student=self.student,
            title="Appeal Request",
            description="Grade appeal",
            request_type=Request.TYPE_APPEAL,
            course=self.course
        )
        
        request.assigned_lecturer = self.lecturer
        request.status = Request.STATUS_SENT_TO_LECTURER
        request.save()
        
        self.assertEqual(request.assigned_lecturer, self.lecturer)
