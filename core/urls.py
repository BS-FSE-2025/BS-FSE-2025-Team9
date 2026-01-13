"""
Core authentication URLs - shared login/logout with 2FA for all roles.
"""
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_with_verification, name="login"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("logout/", views.logout_view, name="logout"),
]
