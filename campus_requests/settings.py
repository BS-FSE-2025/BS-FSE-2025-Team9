"""
Unified Django settings for Student Request Management System.
Combines all 4 branches into one project.
"""

from pathlib import Path
import ssl
import smtplib

# ============================================
# FIX SSL CERTIFICATE VERIFICATION ISSUE
# ============================================
ssl._create_default_https_context = ssl._create_unverified_context

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "dev-secret-key-change-me-in-production"

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# ============================================
# INSTALLED APPS - All unified apps
# ============================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Core apps
    "core",  # User model with 2FA
    "requests_unified",  # Request model and related models
    # Role-specific apps
    "students",  # Student portal
    "staff",  # Staff dashboard
    "lecturers",  # Lecturer dashboard
    "head_of_dept",  # Department head dashboard
    # Admin
    "management",  # Admin user management dashboard
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "campus_requests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "campus_requests.wsgi.application"

# ============================================
# DATABASE
# ============================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ============================================
# CUSTOM USER MODEL
# ============================================
AUTH_USER_MODEL = "core.User"

# ============================================
# PASSWORD VALIDATION
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 7},
    },
    {
        "NAME": "core.validators.StrongPasswordValidator",
    },
]

# ============================================
# AUTHENTICATION
# ============================================
LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "redirect_to_dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# ============================================
# INTERNATIONALIZATION
# ============================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jerusalem"
USE_I18N = True
USE_TZ = True

# ============================================
# STATIC FILES
# ============================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# ============================================
# MEDIA FILES
# ============================================
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ============================================
# DEFAULT PRIMARY KEY
# ============================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ============================================
# EMAIL CONFIGURATION - 2FA Verification Codes
# ============================================
EMAIL_BACKEND = 'core.email_backend.CustomEmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'saied442001@gmail.com'          # <-- Your Gmail address
EMAIL_HOST_PASSWORD = 'qodn omhx djnl tfqd'        # <-- PASTE YOUR NEW APP PASSWORD HERE (16 characters)
DEFAULT_FROM_EMAIL = 'SCE Student Portal <saied442001@gmail.com>'
EMAIL_TIMEOUT = 30
