"""
Core authentication URLs - shared login/logout with 2FA for all roles.
"""
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_with_verification, name="login"),
    path("signup/", views.signup, name="signup"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("logout/", views.logout_view, name="logout"),
]
