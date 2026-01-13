from django.apps import AppConfig


class RequestsUnifiedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests_unified'
    verbose_name = 'Student Requests'
    
    def ready(self):
        # Import signals to register them
        import requests_unified.signals  # noqa: F401
        
        # Initialize default degrees when app starts
        # This ensures degrees exist even without running migrations
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError
        
        try:
            # Check if database is ready and table exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM requests_unified_degree LIMIT 1")
            
            # Database is ready, initialize degrees
            requests_unified.signals.initialize_degrees()
        except (OperationalError, ProgrammingError):
            # Database not ready or table doesn't exist yet
            # Will be created after migrations via post_migrate signal
            pass
        except Exception:
            # Any other error, silently continue
            pass
