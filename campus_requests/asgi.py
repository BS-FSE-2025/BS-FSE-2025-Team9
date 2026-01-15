"""
ASGI config for campus_requests project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'campus_requests.settings')
application = get_asgi_application()
