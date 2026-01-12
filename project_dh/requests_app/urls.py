from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('quick-login/<str:role>/', views.quick_login, name='quick_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('head-dashboard/', views.head_dashboard, name='head_dashboard'),
    
    # API endpoints
    path('api/head/pending-requests/', views.get_pending_requests, name='get_pending_requests'),
    path('api/head/approve-request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('api/head/add-final-notes/<int:request_id>/', views.add_final_notes, name='add_final_notes'),
    path('api/head/request-details/<int:request_id>/', views.get_request_details, name='get_request_details'),
    path('api/head/add-comment/<int:request_id>/', views.add_comment, name='add_comment'),
    path('api/head/statistics/', views.get_statistics, name='get_statistics'),
]
