"""
Student portal URLs.
"""
from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Profile
    path("profile/", views.profile_edit, name="profile_edit"),
    
    # Requests
    path("requests/new/", views.submit_request, name="submit_request"),
    path("requests/new/<str:request_type>/", views.submit_request, name="submit_request_by_type"),
    path("requests/<str:request_id>/", views.request_detail, name="request_detail"),
]
