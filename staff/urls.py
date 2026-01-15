"""
Staff/Secretary URLs.
"""
from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Request management
    path("request/<int:request_id>/", views.request_detail, name="request_detail"),
    path("request/<int:request_id>/add-note/", views.add_note, name="add_note"),
    path("request/<int:request_id>/request-docs/", views.request_docs, name="request_docs"),
    path("request/<int:request_id>/send-to-lecturer/", views.send_to_lecturer, name="send_to_lecturer"),
    path("request/<int:request_id>/send-to-hod/", views.send_to_hod, name="send_to_hod"),
    
    # Missing document management
    path("doc/<int:doc_id>/resolve/", views.resolve_doc, name="resolve_doc"),
]
