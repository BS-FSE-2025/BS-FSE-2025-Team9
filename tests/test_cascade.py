"""
Tests for cascade handling: orphaned requests routed to HOD.
"""
from django.test import TestCase

from core.models import User
from requests_unified.models import Degree, Course, Request, Notification


class CascadeCourseDeleteTest(TestCase):
    """Tests for course deletion cascading."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
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
        
        # Create pending request for this course
        self.pending_request = Request.objects.create(
            student=self.student,
            title="Pending Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_SENT_TO_LECTURER
        )
        
        # Create approved request for this course (should not be affected)
        self.approved_request = Request.objects.create(
            student=self.student,
            title="Approved Request",
            description="Description",
            course=self.course,
            status=Request.STATUS_APPROVED
        )
    
    def test_course_deletion_routes_pending_to_hod(self):
        """Test that deleting a course routes pending requests to HOD."""
        self.course.delete()
        
        self.pending_request.refresh_from_db()
        self.assertEqual(self.pending_request.status, Request.STATUS_SENT_TO_HOD)
    
    def test_course_deletion_ignores_completed_requests(self):
        """Test that completed requests are not affected by course deletion."""
        self.course.delete()
        
        self.approved_request.refresh_from_db()
        self.assertEqual(self.approved_request.status, Request.STATUS_APPROVED)
    
    def test_course_deletion_creates_notification(self):
        """Test that a notification is created for affected students."""
        initial_count = Notification.objects.filter(user=self.student).count()
        
        self.course.delete()
        
        new_count = Notification.objects.filter(user=self.student).count()
        self.assertEqual(new_count, initial_count + 1)
        
        notification = Notification.objects.filter(user=self.student).first()
        self.assertIn("routed to the Head of Department", notification.message)


class CascadeLecturerRemovedFromCourseTest(TestCase):
    """Tests for lecturer removal from course."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
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
        
        # Create request assigned to this lecturer
        self.request = Request.objects.create(
            student=self.student,
            title="Request",
            description="Description",
            course=self.course,
            assigned_lecturer=self.lecturer,
            status=Request.STATUS_SENT_TO_LECTURER
        )
    
    def test_lecturer_removal_routes_to_hod(self):
        """Test that removing lecturer from course routes their requests to HOD."""
        self.course.lecturers.remove(self.lecturer)
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_SENT_TO_HOD)


class CascadeLecturerDeleteTest(TestCase):
    """Tests for lecturer account deletion."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
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
        
        # Create request assigned to this lecturer
        self.request = Request.objects.create(
            student=self.student,
            title="Request",
            description="Description",
            course=self.course,
            assigned_lecturer=self.lecturer,
            status=Request.STATUS_SENT_TO_LECTURER
        )
    
    def test_lecturer_deletion_routes_to_hod(self):
        """Test that deleting a lecturer routes their requests to HOD."""
        self.lecturer.delete()
        
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Request.STATUS_SENT_TO_HOD)


class CascadeMultipleRequestsTest(TestCase):
    """Tests for cascade with multiple pending requests."""
    
    def setUp(self):
        self.degree = Degree.objects.create(name="Software Engineering", code="SE")
        self.course = Course.objects.create(code="SE101", name="Course 1")
        self.course.degrees.add(self.degree)
        
        self.lecturer = User.objects.create_user(
            username="lecturer1",
            email="lecturer1@sce.ac.il",
            password="Test123!",
            role=User.ROLE_LECTURER,
            first_name="John",
            last_name="Lecturer"
        )
        self.course.lecturers.add(self.lecturer)
        
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
        
        # Create multiple requests with different statuses
        self.requests = [
            Request.objects.create(
                student=self.student,
                title=f"Request {i}",
                description="Description",
                course=self.course,
                status=status
            )
            for i, status in enumerate([
                Request.STATUS_NEW,
                Request.STATUS_IN_PROGRESS,
                Request.STATUS_SENT_TO_LECTURER,
                Request.STATUS_NEEDS_INFO,
                Request.STATUS_APPROVED,
                Request.STATUS_REJECTED,
            ])
        ]
    
    def test_only_pending_requests_affected(self):
        """Test that only pending (not completed) requests are routed to HOD."""
        self.course.delete()
        
        for req in self.requests:
            req.refresh_from_db()
        
        # First 4 should be routed to HOD (pending statuses)
        self.assertEqual(self.requests[0].status, Request.STATUS_SENT_TO_HOD)
        self.assertEqual(self.requests[1].status, Request.STATUS_SENT_TO_HOD)
        self.assertEqual(self.requests[2].status, Request.STATUS_SENT_TO_HOD)
        self.assertEqual(self.requests[3].status, Request.STATUS_SENT_TO_HOD)
        
        # Last 2 should remain unchanged (completed statuses)
        self.assertEqual(self.requests[4].status, Request.STATUS_APPROVED)
        self.assertEqual(self.requests[5].status, Request.STATUS_REJECTED)
