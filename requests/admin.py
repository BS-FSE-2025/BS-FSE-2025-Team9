from django.contrib import admin
from .models import Student, StudentRequest, Attachment

admin.site.register(Student)
admin.site.register(StudentRequest)
admin.site.register(Attachment)
