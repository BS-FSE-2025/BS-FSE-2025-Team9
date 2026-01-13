"""
Tests for access control: role-based permissions.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request


class StudentAccessControlTest(TestCase):
    """Tests for student access restrictions."""
    
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
        
        self.other_student = User.objects.create_user(
            username="other_student",
            email="other@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Other",
            last_name="Student",
            student_id="987654321",
            degree=self.degree
        )
        
        self.other_request = Request.objects.create(
            student=self.other_student,
            title="Other's Request",
            description="Description",
            status=Request.STATUS_NEW
        )
        
        self.client.force_login(self.student)
    
    def test_student_cannot_access_staff_dashboard(self):
        """Test student cannot access staff dashboard."""
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 302)  # Redirected
    
    def test_student_cannot_access_lecturer_dashboard(self):
        """Test student cannot access lecturer dashboard."""
        response = self.client.get(reverse('lecturers:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_student_cannot_access_hod_dashboard(self):
        """Test student cannot access HOD dashboard."""
        response = self.client.get(reverse('head_of_dept:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_student_cannot_access_management(self):
        """Test student cannot access management panel."""
        response = self.client.get(reverse('management:user_list'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_student_cannot_view_others_requests(self):
        """Test student cannot view other student's request details."""
        response = self.client.get(
            reverse('students:request_detail', args=[self.other_request.request_id])
        )
        
        self.assertEqual(response.status_code, 404)


class SecretaryAccessControlTest(TestCase):
    """Tests for secretary access restrictions."""
    
    def setUp(self):
        self.client = Client()
        
        self.secretary = User.objects.create_user(
            username="secretary",
            email="secretary@sce.ac.il",
            password="Test123!",
            role=User.ROLE_SECRETARY,
            first_name="Sara",
            last_name="Secretary"
        )
        
        self.client.force_login(self.secretary)
    
    def test_secretary_can_access_staff_dashboard(self):
        """Test secretary can access staff dashboard."""
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_secretary_cannot_access_lecturer_dashboard(self):
        """Test secretary cannot access lecturer dashboard."""
        response = self.client.get(reverse('lecturers:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_secretary_cannot_access_hod_dashboard(self):
        """Test secretary cannot access HOD dashboard."""
        response = self.client.get(reverse('head_of_dept:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_secretary_can_access_degree_management(self):
        """Test secretary can access degree management."""
        response = self.client.get(reverse('management:degree_list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_secretary_can_access_course_management(self):
        """Test secretary can access course management."""
        response = self.client.get(reverse('management:course_list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_secretary_cannot_access_user_management(self):
        """Test secretary cannot access user management."""
        response = self.client.get(reverse('management:user_list'))
        
        self.assertEqual(response.status_code, 302)


class LecturerAccessControlTest(TestCase):
    """Tests for lecturer access restrictions."""
    
    def setUp(self):
        self.client = Client()
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        
        self.client.force_login(self.lecturer)
    
    def test_lecturer_can_access_lecturer_dashboard(self):
        """Test lecturer can access lecturer dashboard."""
        response = self.client.get(reverse('lecturers:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_lecturer_cannot_access_staff_dashboard(self):
        """Test lecturer cannot access staff dashboard."""
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_lecturer_cannot_access_hod_dashboard(self):
        """Test lecturer cannot access HOD dashboard."""
        response = self.client.get(reverse('head_of_dept:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_lecturer_cannot_access_management(self):
        """Test lecturer cannot access management panel."""
        response = self.client.get(reverse('management:user_list'))
        
        self.assertEqual(response.status_code, 302)


class HODAccessControlTest(TestCase):
    """Tests for HOD access restrictions."""
    
    def setUp(self):
        self.client = Client()
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Dept"
        )
        
        self.client.force_login(self.hod)
    
    def test_hod_can_access_hod_dashboard(self):
        """Test HOD can access HOD dashboard."""
        response = self.client.get(reverse('head_of_dept:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_hod_can_access_degree_management(self):
        """Test HOD can access degree management."""
        response = self.client.get(reverse('management:degree_list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_hod_can_access_course_management(self):
        """Test HOD can access course management."""
        response = self.client.get(reverse('management:course_list'))
        
        self.assertEqual(response.status_code, 200)


class AdminAccessControlTest(TestCase):
    """Tests for admin access - should have full access."""
    
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
    
    def test_admin_can_access_management_dashboard(self):
        """Test admin can access management dashboard."""
        response = self.client.get(reverse('management:dashboard'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_access_user_management(self):
        """Test admin can access user management."""
        response = self.client.get(reverse('management:user_list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_access_degree_management(self):
        """Test admin can access degree management."""
        response = self.client.get(reverse('management:degree_list'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_admin_can_access_course_management(self):
        """Test admin can access course management."""
        response = self.client.get(reverse('management:course_list'))
        
        self.assertEqual(response.status_code, 200)


class UnauthenticatedAccessTest(TestCase):
    """Tests for unauthenticated access restrictions."""
    
    def setUp(self):
        self.client = Client()
    
    def test_homepage_accessible_without_login(self):
        """Test homepage is accessible without login."""
        response = self.client.get(reverse('core:home'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_accessible_without_login(self):
        """Test login page is accessible without login."""
        response = self.client.get(reverse('core:login'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_signup_page_accessible_without_login(self):
        """Test signup page is accessible without login."""
        response = self.client.get(reverse('core:signup'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_student_dashboard_requires_login(self):
        """Test student dashboard requires login."""
        response = self.client.get(reverse('students:dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_staff_dashboard_requires_login(self):
        """Test staff dashboard requires login."""
        response = self.client.get(reverse('staff:dashboard'))
        
        self.assertEqual(response.status_code, 302)
    
    def test_management_requires_login(self):
        """Test management panel requires login."""
        response = self.client.get(reverse('management:dashboard'))
        
        self.assertEqual(response.status_code, 302)
