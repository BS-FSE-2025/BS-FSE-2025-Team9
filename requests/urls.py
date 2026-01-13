from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("create/", views.create_request, name="create_request"),
    path("request/<int:pk>/", views.request_detail_partial, name="request_detail_partial"),
    path("api/update-status/<int:pk>/", views.update_status, name="update_status"),
]
