"""
Head of Department URLs.
"""
from django.urls import path
from . import views

app_name = "head_of_dept"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Statistics
    path("statistics/", views.statistics, name="statistics"),
    
    # Request management
    path("request/<int:request_id>/", views.request_detail, name="request_detail"),
    path("request/<int:request_id>/approve/", views.approve_request, name="approve"),
    path("request/<int:request_id>/reject/", views.reject_request, name="reject"),
    path("request/<int:request_id>/add-notes/", views.add_final_notes, name="add_notes"),
    path("request/<int:request_id>/add-comment/", views.add_comment, name="add_comment"),
    
    # API endpoints (JSON responses)
    path("api/pending-requests/", views.api_pending_requests, name="api_pending_requests"),
    path("api/statistics/", views.api_statistics, name="api_statistics"),
]
