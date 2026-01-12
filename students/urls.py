from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "students"

urlpatterns = [
    # Authentication - NO SIGNUP!
    path("login/", views.login_with_verification, name="login"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("logout/", views.logout_view, name="logout"),
    
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Profile
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    
    # Requests
    path("requests/new/", views.submit_request, name="submit_request"),
    path("requests/new/<str:request_type>/", views.submit_request, name="submit_request_by_type"),
    path("requests/<str:request_id>/", views.request_detail, name="request_detail"),
]






























