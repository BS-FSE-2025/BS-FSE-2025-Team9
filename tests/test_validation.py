"""
Tests for validation: email, student ID, form validation.
"""
from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.urls import reverse

from core.validators import validate_sce_email
from core.models import User
from requests_unified.models import Degree


class EmailValidationTest(TestCase):
    """Tests for SCE email validation."""
    
    def test_valid_sce_email(self):
        """Test valid @sce.ac.il email passes validation."""
        try:
            validate_sce_email('student@sce.ac.il')
        except ValidationError:
            self.fail("validate_sce_email raised ValidationError unexpectedly")
    
    def test_valid_ac_sce_email(self):
        """Test valid @ac.sce.ac.il email passes validation."""
        try:
            validate_sce_email('student@ac.sce.ac.il')
        except ValidationError:
            self.fail("validate_sce_email raised ValidationError unexpectedly")
    
    def test_invalid_gmail_email(self):
        """Test @gmail.com email fails validation."""
        with self.assertRaises(ValidationError):
            validate_sce_email('student@gmail.com')
    
    def test_invalid_random_email(self):
        """Test random domain email fails validation."""
        with self.assertRaises(ValidationError):
            validate_sce_email('student@random.org')
    
    def test_partial_match_fails(self):
        """Test partial domain match fails validation."""
        with self.assertRaises(ValidationError):
            validate_sce_email('student@fake-sce.ac.il')


class StudentIDValidationTest(TestCase):
    """Tests for student ID validation."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
    
    def test_valid_9_digit_id(self):
        """Test 9-digit ID is accepted."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(student_id='123456789').exists())
    
    def test_short_id_rejected(self):
        """Test ID with less than 9 digits is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '12345',  # Only 5 digits
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "9 digits")
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())
    
    def test_long_id_rejected(self):
        """Test ID with more than 9 digits is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '1234567890',  # 10 digits
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "9 digits")
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())
    
    def test_alphanumeric_id_rejected(self):
        """Test alphanumeric ID is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '12345678A',  # Contains letter
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())


class PasswordValidationTest(TestCase):
    """Tests for password validation on signup."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
    
    def test_password_mismatch_rejected(self):
        """Test mismatched passwords are rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Different123!',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "match")
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())
    
    def test_weak_password_rejected(self):
        """Test weak password is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': '12345',
            'confirm_password': '12345',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='john.doe@sce.ac.il').exists())


class DuplicateUserTest(TestCase):
    """Tests for duplicate user prevention."""
    
    def setUp(self):
        self.client = Client()
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        
        self.existing_user = User.objects.create_user(
            username="existing",
            email="existing@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Existing",
            last_name="User",
            student_id="111111111"
        )
    
    def test_duplicate_email_rejected(self):
        """Test duplicate email is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'existing@sce.ac.il',  # Already exists
            'student_id': '123456789',
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already")
    
    def test_duplicate_student_id_rejected(self):
        """Test duplicate student ID is rejected."""
        response = self.client.post(reverse('core:signup'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@sce.ac.il',
            'student_id': '111111111',  # Already exists
            'degree': self.degree.id,
            'password': 'Test123!@#',
            'confirm_password': 'Test123!@#',
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already")
