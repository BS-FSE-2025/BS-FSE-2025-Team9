"""
Lecturer URLs.
"""
from django.urls import path
from . import views

app_name = "lecturers"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Request management
    path("request/<int:request_id>/", views.request_detail, name="request_detail"),
    path("request/<int:request_id>/approve/", views.approve_request, name="approve"),
    path("request/<int:request_id>/reject/", views.reject_request, name="reject"),
    path("request/<int:request_id>/needs-info/", views.needs_info, name="needs_info"),
    path("request/<int:request_id>/forward-to-hod/", views.forward_to_hod, name="forward_to_hod"),
]
