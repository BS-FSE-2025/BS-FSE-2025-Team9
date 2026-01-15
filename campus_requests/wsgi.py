"""
WSGI config for campus_requests project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_requests.settings')
application = get_wsgi_application()
