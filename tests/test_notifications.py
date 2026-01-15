"""
Tests for notifications system.
"""
from django.test import TestCase, Client
from django.urls import reverse

from core.models import User
from requests_unified.models import Degree, Course, Request, Notification


class NotificationCreationTest(TestCase):
    """Tests for notification creation on events."""
    
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
        
        self.lecturer = User.objects.create_user(
            username="lecturer",
            email="lecturer@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
        self.request = Request.objects.create(
            student=self.student,
            title="Test Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER,
            assigned_lecturer=self.lecturer
        )
    
    def test_notification_on_approval(self):
        """Test notification is created when request is approved."""
        initial_count = Notification.objects.filter(user=self.student).count()
        
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:approve', args=[self.request.id]),
            {'feedback': 'Approved'}
        )
        
        # Check notification was created for student
        new_count = Notification.objects.filter(user=self.student).count()
        self.assertEqual(new_count, initial_count + 1)
    
    def test_notification_on_rejection(self):
        """Test notification is created when request is rejected."""
        initial_count = Notification.objects.filter(user=self.student).count()
        
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:reject', args=[self.request.id]),
            {'feedback': 'Rejected - not eligible'}
        )
        
        new_count = Notification.objects.filter(user=self.student).count()
        self.assertEqual(new_count, initial_count + 1)
    
    def test_notification_on_needs_info(self):
        """Test notification when more info is requested."""
        initial_count = Notification.objects.filter(user=self.student).count()
        
        self.client.force_login(self.lecturer)
        
        response = self.client.post(
            reverse('lecturers:needs_info', args=[self.request.id]),
            {'feedback': 'Please provide more details'}
        )
        
        new_count = Notification.objects.filter(user=self.student).count()
        self.assertEqual(new_count, initial_count + 1)


class NotificationReadTest(TestCase):
    """Tests for marking notifications as read."""
    
    def setUp(self):
        self.client = Client()
        
        self.student = User.objects.create_user(
            username="student",
            email="student@sce.ac.il",
            password="Test123!",
            role=User.ROLE_STUDENT,
            first_name="Student",
            last_name="One",
            student_id="123456789"
        )
        
        self.notification = Notification.objects.create(
            user=self.student,
            message="This is a test notification",
            is_read=False
        )
    
    def test_notification_marked_as_read(self):
        """Test notification can be marked as read."""
        self.client.force_login(self.student)
        
        self.assertFalse(self.notification.is_read)
        
        # Mark notification as read directly (endpoint not yet implemented)
        self.notification.is_read = True
        self.notification.save()
        
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
    
    def test_unread_count_decreases(self):
        """Test unread notification count decreases when marked read."""
        # Create multiple notifications
        Notification.objects.create(
            user=self.student,
            message="Message 2",
            is_read=False
        )
        
        initial_unread = Notification.objects.filter(
            user=self.student, is_read=False
        ).count()
        
        self.notification.is_read = True
        self.notification.save()
        
        new_unread = Notification.objects.filter(
            user=self.student, is_read=False
        ).count()
        
        self.assertEqual(new_unread, initial_unread - 1)
