"""
Tests for management: degree/course CRUD, access control.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course


class ManagementAccessControlTest(TestCase):
    """Tests for management panel access control."""
    
    def setUp(self):
        self.client = Client()
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        # Create users with different roles
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        self.secretary = User.objects.create_user(
            username="secretary",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Dept"
        )
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        
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
    
    def test_admin_can_access_user_management(self):
        """Test that admin can access user management."""
        self.client.force_login(self.admin)
        
        response = self.client.get(reverse('management:user_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_student_cannot_access_user_management(self):
        """Test that student cannot access user management."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('management:user_list'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_admin_can_access_degree_management(self):
        """Test that admin can access degree management."""
        self.client.force_login(self.admin)
        
        response = self.client.get(reverse('management:degree_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_secretary_can_access_degree_management(self):
        """Test that secretary can access degree management."""
        self.client.force_login(self.secretary)
        
        response = self.client.get(reverse('management:degree_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_hod_can_access_degree_management(self):
        """Test that HOD can access degree management."""
        self.client.force_login(self.hod)
        
        response = self.client.get(reverse('management:degree_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_lecturer_cannot_access_degree_management(self):
        """Test that lecturer cannot access degree management."""
        self.client.force_login(self.lecturer)
        
        response = self.client.get(reverse('management:degree_list'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_student_cannot_access_degree_management(self):
        """Test that student cannot access degree management."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('management:degree_list'))
        self.assertEqual(response.status_code, 302)  # Redirect


class DegreeCRUDTest(TestCase):
    """Tests for Degree CRUD operations."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        self.client.force_login(self.admin)
    
    def test_create_degree(self):
        """Test creating a degree."""
        response = self.client.post(reverse('management:degree_add'), {
            'name': 'Software Engineering',
            'code': 'SE',
            'is_active': 'on',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Degree.objects.filter(code='SE').exists())
    
    def test_update_degree(self):
        """Test updating a degree."""
        degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        response = self.client.post(
            reverse('management:degree_edit', args=[degree.id]),
            {
                'name': 'Software Engineering Updated',
                'code': 'SE',
                'is_active': 'on',
            }
        )
        
        self.assertEqual(response.status_code, 302)
        degree.refresh_from_db()
        self.assertEqual(degree.name, 'Software Engineering Updated')
    
    def test_delete_degree(self):
        """Test deleting a degree."""
        degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        response = self.client.post(
            reverse('management:degree_delete', args=[degree.id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Degree.objects.filter(code='SE').exists())


class CourseCRUDTest(TestCase):
    """Tests for Course CRUD operations."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        self.client.force_login(self.admin)
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
    
    def test_create_course_with_degree(self):
        """Test creating a course with degree assignment."""
        response = self.client.post(reverse('management:course_add'), {
            'name': 'Intro to Programming',
            'code': 'CS101',
            'degrees': [self.degree.id],
            'is_active': 'on',
        })
        
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(code='CS101')
        self.assertIn(self.degree, course.degrees.all())
    
    def test_create_course_requires_degree(self):
        """Test that creating a course requires at least one degree."""
        response = self.client.post(reverse('management:course_add'), {
            'name': 'Intro to Programming',
            'code': 'CS101',
            'degrees': [],  # No degree
            'is_active': 'on',
        })
        
        # Should stay on page with error
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Course.objects.filter(code='CS101').exists())
    
    def test_create_course_with_lecturer(self):
        """Test creating a course with lecturer assignment."""
        response = self.client.post(reverse('management:course_add'), {
            'name': 'Intro to Programming',
            'code': 'CS101',
            'degrees': [self.degree.id],
            'lecturers': [self.lecturer.id],
            'is_active': 'on',
        })
        
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(code='CS101')
        self.assertIn(self.lecturer, course.lecturers.all())
    
    def test_update_course(self):
        """Test updating a course."""
        course = Course.objects.create(name="Intro", code="CS101")
        course.degrees.add(self.degree)
        
        response = self.client.post(
            reverse('management:course_edit', args=[course.id]),
            {
                'name': 'Introduction to Programming',
                'code': 'CS101',
                'degrees': [self.degree.id],
                'is_active': 'on',
            }
        )
        
        self.assertEqual(response.status_code, 302)
        course.refresh_from_db()
        self.assertEqual(course.name, 'Introduction to Programming')
    
    def test_delete_course(self):
        """Test deleting a course."""
        course = Course.objects.create(name="Intro", code="CS101")
        course.degrees.add(self.degree)
        
        response = self.client.post(
            reverse('management:course_delete', args=[course.id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(code='CS101').exists())
