from django.core.management.base import BaseCommand
from requests_app.models import Request, User

class Command(BaseCommand):
    help = 'Create demo users and sample requests'

    def handle(self, *args, **options):
        # Create demo users
        roles = [
            ('head@example.com', 'head_of_dept', 'Department Head', 'Computer Science'),
            ('student@example.com', 'student', 'John Student', 'Computer Science'),
            ('secretary@example.com', 'secretary', 'Jane Secretary', 'Computer Science'),
            ('lecturer@example.com', 'lecturer', 'Dr. Smith Lecturer', 'Computer Science'),
        ]
        
        for email, role, name, department in roles:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'role': role,
                    'name': name,
                    'department': department,
                }
            )
            if created:
                user.set_password('password')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {name} ({role})'))
            else:
                self.stdout.write(self.style.WARNING(f'User already exists: {name}'))
        
        # Create sample requests
        student = User.objects.filter(role='student').first()
        if student and Request.objects.count() == 0:
            requests_data = [
                {
                    'student': student,
                    'request_type': 'Study Approval',
                    'title': 'Request for Course Overload',
                    'description': 'I would like to request approval to take 6 courses this semester.',
                    'priority': 'high'
                },
                {
                    'student': student,
                    'request_type': 'Appeal',
                    'title': 'Grade Appeal Request',
                    'description': 'I would like to appeal my grade in CS101.',
                    'priority': 'medium'
                },
                {
                    'student': student,
                    'request_type': 'Postponement',
                    'title': 'Exam Postponement Request',
                    'description': 'I need to postpone my final exam due to medical reasons.',
                    'priority': 'high'
                },
                {
                    'student': student,
                    'request_type': 'General',
                    'title': 'General Inquiry',
                    'description': 'I have a question about the curriculum.',
                    'priority': 'low'
                }
            ]
            
            for req_data in requests_data:
                Request.objects.create(**req_data)
                self.stdout.write(self.style.SUCCESS(f'Created request: {req_data["title"]}'))
        
        self.stdout.write(self.style.SUCCESS('Demo data creation completed!'))
