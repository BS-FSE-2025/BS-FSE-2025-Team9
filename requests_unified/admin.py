from django.contrib import admin
from .models import (
    Request, StatusHistory, StaffNote, RequestDocument,
    MissingDocument, Comment, ApprovalLog, Notification
)


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'title', 'student', 'request_type', 'status', 'priority', 'created_at')
    list_filter = ('status', 'request_type', 'priority', 'created_at')
    search_fields = ('request_id', 'title', 'student__email', 'student__username')
    readonly_fields = ('request_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'title', 'description', 'request_type', 'priority')
        }),
        ('Student', {
            'fields': ('student',)
        }),
        ('Status', {
            'fields': ('status', 'final_notes', 'lecturer_feedback')
        }),
        ('Course Info', {
            'fields': ('course_name', 'related_course', 'reason'),
            'classes': ('collapse',)
        }),
        ('Assignments', {
            'fields': ('assigned_staff', 'assigned_lecturer', 'head_of_dept'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'status', 'role', 'changed_by', 'created_at')
    list_filter = ('status', 'role', 'created_at')
    search_fields = ('request__request_id',)


@admin.register(StaffNote)
class StaffNoteAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('request__request_id', 'note')


@admin.register(RequestDocument)
class RequestDocumentAdmin(admin.ModelAdmin):
    list_display = ('request', 'file', 'uploaded_by', 'uploaded_by_student', 'uploaded_at')
    list_filter = ('uploaded_by_student', 'uploaded_at')
    search_fields = ('request__request_id', 'filename')


@admin.register(MissingDocument)
class MissingDocumentAdmin(admin.ModelAdmin):
    list_display = ('request', 'doc_name', 'resolved', 'requested_by', 'created_at')
    list_filter = ('resolved', 'created_at')
    search_fields = ('request__request_id', 'doc_name')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('request__request_id', 'comment')


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ('request', 'approver', 'action', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('request__request_id', 'notes')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'request', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__email', 'message')
