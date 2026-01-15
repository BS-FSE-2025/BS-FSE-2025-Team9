"""
Tests for authentication: login, logout, verification codes.
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

from core.models import User
from requests_unified.models import Degree


class LoginTest(TestCase):
    """Tests for login flow."""
    
    def setUp(self):
        self.client = Client()
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789"
        )
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
    
    def test_login_page_accessible(self):
        """Test login page is accessible."""
        response = self.client.get(reverse('core:login'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials triggers verification code."""
        with patch('core.views.send_mail') as mock_send:
            mock_send.return_value = 1  # send_mail returns number of messages sent
            
            response = self.client.post(reverse('core:login'), {
                'email': 'student1@sce.ac.il',
                'password': 'Test123!',
            })
            
            # Should redirect to verify code page
            self.assertEqual(response.status_code, 302)
            self.assertIn('verify', response.url)
    
    def test_login_with_invalid_password(self):
        """Test login with wrong password shows error."""
        response = self.client.post(reverse('core:login'), {
            'email': 'student1@sce.ac.il',
            'password': 'WrongPassword!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")
    
    def test_login_with_nonexistent_user(self):
        """Test login with nonexistent email shows error."""
        response = self.client.post(reverse('core:login'), {
            'email': 'nonexistent@sce.ac.il',
            'password': 'Test123!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")


class VerificationCodeTest(TestCase):
    """Tests for 2FA verification code flow."""
    
    def setUp(self):
        self.client = Client()
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789"
        )
    
    def test_verify_code_page_requires_session(self):
        """Test verify code page redirects without session."""
        response = self.client.get(reverse('core:verify_code'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_verify_with_correct_code(self):
        """Test verification with correct code logs in user."""
        from core.models import VerificationCode
        from django.utils import timezone
        from datetime import timedelta
        
        # Set up session manually
        session = self.client.session
        session['pending_user_id'] = self.student.id
        session.save()
        
        # Create verification code in the database
        VerificationCode.objects.create(
            user=self.student,
            code='123456',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_used=False
        )
        
        response = self.client.post(reverse('core:verify_code'), {
            'code': '123456',
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
    
    def test_verify_with_wrong_code(self):
        """Test verification with wrong code shows error."""
        session = self.client.session
        session['pending_user_id'] = self.student.id
        session['verification_code'] = '123456'
        session.save()
        
        response = self.client.post(reverse('core:verify_code'), {
            'code': '000000',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")


class LogoutTest(TestCase):
    """Tests for logout flow."""
    
    def setUp(self):
        self.client = Client()
        
        self.student = User.objects.create_user(
            username="student1",
            email="student1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789"
        )
    
    def test_logout_clears_session(self):
        """Test logout clears session and redirects."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('core:logout'))
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        
        # Check user is logged out
        response = self.client.get(reverse('students:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected to login


class RoleBasedRedirectTest(TestCase):
    """Tests for role-based dashboard redirects."""
    
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
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        
        self.hod = User.objects.create_user(
            username="hod",
            email="hod@sce.ac.il",
            password="Test123!",
            role=User.ROLE_HEAD_OF_DEPT,
            first_name="Head",
            last_name="Dept"
        )
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
    
    def test_student_redirects_to_student_dashboard(self):
        """Test student redirects to student dashboard."""
        self.client.force_login(self.student)
        
        response = self.client.get(reverse('redirect_to_dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('students', response.url)
    
    def test_secretary_redirects_to_staff_dashboard(self):
        """Test secretary redirects to staff dashboard."""
        self.client.force_login(self.secretary)
        
        response = self.client.get(reverse('redirect_to_dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('staff', response.url)
    
    def test_lecturer_redirects_to_lecturer_dashboard(self):
        """Test lecturer redirects to lecturer dashboard."""
        self.client.force_login(self.lecturer)
        
        response = self.client.get(reverse('redirect_to_dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('lecturers', response.url)
    
    def test_hod_redirects_to_hod_dashboard(self):
        """Test HOD redirects to HOD dashboard."""
        self.client.force_login(self.hod)
        
        response = self.client.get(reverse('redirect_to_dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('head', response.url)
    
    def test_admin_redirects_to_management_dashboard(self):
        """Test admin redirects to management dashboard."""
        self.client.force_login(self.admin)
        
        response = self.client.get(reverse('redirect_to_dashboard'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('management', response.url)
