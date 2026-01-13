"""
URL configuration for management app.
"""
from django.urls import path
from . import views

app_name = 'management'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # User management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Degree management
    path('degrees/', views.degree_list, name='degree_list'),
    path('degrees/add/', views.degree_add, name='degree_add'),
    path('degrees/<int:degree_id>/edit/', views.degree_edit, name='degree_edit'),
    path('degrees/<int:degree_id>/delete/', views.degree_delete, name='degree_delete'),
    
    # Course management
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<int:course_id>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
]
