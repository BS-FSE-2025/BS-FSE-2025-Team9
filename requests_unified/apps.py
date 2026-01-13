from django.apps import AppConfig


class RequestsUnifiedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests_unified'
    verbose_name = 'Student Requests'
    
    def ready(self):
        # Import signals to register them
        # The post_migrate signal will initialize default degrees
        import requests_unified.signals  # noqa: F401
