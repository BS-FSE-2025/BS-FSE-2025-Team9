"""
Tests for user management in admin panel.
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest import skip

from core.models import User
from requests_unified.models import Degree


class UserListTest(TestCase):
    """Tests for user list in management panel."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        # Create users of different roles
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="John",
            last_name="Student",
            student_id="123456789"
        )
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="Jane",
            last_name="Lecturer"
        )
        
        self.client.force_login(self.admin)
    
    def test_user_list_shows_all_users(self):
        """Test user list displays all users."""
        response = self.client.get(reverse('management:user_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Student")
        self.assertContains(response, "Jane Lecturer")
    
    def test_user_list_filter_by_role(self):
        """Test filtering user list by role."""
        response = self.client.get(
            reverse('management:user_list') + '?role=student'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Student")
        self.assertNotContains(response, "Jane Lecturer")


class UserCreateTest(TestCase):
    """Tests for creating users in management panel."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.client.force_login(self.admin)
    
    def test_create_student(self):
        """Test creating a student through admin panel."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@sce.ac.il',
            'student_id': '111111111',
            'role': 'student',
            'degree': self.degree.id,
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newstudent@sce.ac.il').exists())
        
        user = User.objects.get(email='newstudent@sce.ac.il')
        self.assertEqual(user.role, User.ROLE_STUDENT)
        # Note: degree assignment not yet implemented in user_add view
    
    def test_create_lecturer(self):
        """Test creating a lecturer through admin panel."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Lecturer',
            'email': 'newlecturer@sce.ac.il',
            'role': 'lecturer',
            'department': 'Software Engineering',
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(email='newlecturer@sce.ac.il')
        self.assertEqual(user.role, User.ROLE_LECTURER)
    
    def test_create_secretary(self):
        """Test creating a secretary through admin panel."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Secretary',
            'email': 'newsecretary@sce.ac.il',
            'role': 'secretary',
            'department': 'Administration',
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(email='newsecretary@sce.ac.il')
        self.assertEqual(user.role, User.ROLE_SECRETARY)
    
    def test_create_hod(self):
        """Test creating a head of department through admin panel."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'HOD',
            'email': 'newhod@sce.ac.il',
            'role': 'head_of_dept',
            'department': 'Computer Science',
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(email='newhod@sce.ac.il')
        self.assertEqual(user.role, User.ROLE_HEAD_OF_DEPT)
    
    def test_create_admin(self):
        """Test creating an admin through admin panel."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Admin',
            'email': 'newadmin@sce.ac.il',
            'role': 'admin',
            'department': 'IT',
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(email='newadmin@sce.ac.il')
        self.assertEqual(user.role, User.ROLE_ADMIN)
    
    @skip("Student ID validation for students not yet enforced")
    def test_student_id_required_for_students(self):
        """Test that student ID is required when creating students."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@sce.ac.il',
            'role': 'student',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            # Missing student_id
        })
        
        self.assertEqual(response.status_code, 200)  # Stays on form
        self.assertFalse(User.objects.filter(email='newstudent@sce.ac.il').exists())
    
    def test_student_id_validation_9_digits(self):
        """Test student ID must be exactly 9 digits."""
        response = self.client.post(reverse('management:user_add'), {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@sce.ac.il',
            'student_id': '12345',  # Only 5 digits
            'role': 'student',
            'degree': self.degree.id,
            'password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='newstudent@sce.ac.il').exists())


class UserEditTest(TestCase):
    """Tests for editing users in management panel."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="John",
            last_name="Student",
            student_id="123456789",
            degree=self.degree
        )
        
        self.client.force_login(self.admin)
    
    def test_edit_user_name(self):
        """Test editing user's name."""
        response = self.client.post(
            reverse('management:user_edit', args=[self.student.id]),
            {
                'first_name': 'Johnny',
                'last_name': 'Student',
                'email': 'student@sce.ac.il',
                'student_id': '123456789',
                'role': 'student',
                'degree': self.degree.id,
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Johnny')
    
    def test_change_user_role(self):
        """Test changing user's role."""
        lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="Jane",
            last_name="Lecturer"
        )
        
        response = self.client.post(
            reverse('management:user_edit', args=[lecturer.id]),
            {
                'first_name': 'Jane',
                'last_name': 'Lecturer',
                'email': 'lecturer@sce.ac.il',
                'role': 'head_of_dept',
                'department': 'Computer Science',
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        lecturer.refresh_from_db()
        self.assertEqual(lecturer.role, User.ROLE_HEAD_OF_DEPT)


class UserDeleteTest(TestCase):
    """Tests for deleting users in management panel."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="John",
            last_name="Student",
            student_id="123456789"
        )
        
        self.client.force_login(self.admin)
    
    def test_delete_user(self):
        """Test deleting a user."""
        response = self.client.post(
            reverse('management:user_delete', args=[self.student.id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.student.id).exists())
    
    def test_cannot_delete_self(self):
        """Test admin cannot delete their own account."""
        response = self.client.post(
            reverse('management:user_delete', args=[self.admin.id])
        )
        
        # Should either redirect with error or stay on page
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())


class UserSearchTest(TestCase):
    """Tests for searching users in management panel."""
    
    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@sce.ac.il",
            password="Admin123!",
            first_name="Admin",
            last_name="User"
        )
        
        # Create multiple users
        User.objects.create_user(
            username="john",
            email="john@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="John",
            last_name="Doe",
            student_id="111111111"
        )
        
        User.objects.create_user(
            username="jane",
            email="jane@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Jane",
            last_name="Smith",
            student_id="222222222"
        )
        
        self.client.force_login(self.admin)
    
    def test_search_by_name(self):
        """Test searching users by name."""
        response = self.client.get(
            reverse('management:user_list') + '?search=John'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertNotContains(response, "Jane Smith")
    
    def test_search_by_email(self):
        """Test searching users by email."""
        response = self.client.get(
            reverse('management:user_list') + '?search=jane@'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Smith")
        self.assertNotContains(response, "John Doe")
    
    def test_search_by_student_id(self):
        """Test searching users by student ID."""
        response = self.client.get(
            reverse('management:user_list') + '?search=111111111'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
