from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Request, ApprovalLog, Notification, Comment

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'role', 'department', 'is_staff']
    list_filter = ['role', 'department']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'name', 'department')}),
    )

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'request_type', 'status', 'priority', 'created_at']
    list_filter = ['status', 'request_type', 'priority', 'created_at']
    search_fields = ['title', 'description', 'student__name', 'student__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['request', 'approver', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'read', 'created_at']
    list_filter = ['read', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['request', 'author', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['comment', 'request__title', 'author__name']
    readonly_fields = ['created_at', 'updated_at']
