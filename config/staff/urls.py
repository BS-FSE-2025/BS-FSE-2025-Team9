from django.urls import path
from . import views

app_name = "staff"

urlpatterns = [
    path("requests/", views.request_list, name="request_list"),
    path("requests/<int:request_id>/", views.request_detail, name="request_detail"),
    path("requests/<int:request_id>/add-note/", views.add_note, name="add_note"),
    path("requests/<int:request_id>/request-docs/", views.request_docs, name="request_docs"),
    path("requests/<int:request_id>/send-to-hod/", views.send_to_hod, name="send_to_hod"),
    path("missing-docs/<int:doc_id>/resolve/", views.resolve_doc, name="resolve_doc"),
    
]