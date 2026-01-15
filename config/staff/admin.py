from django.contrib import admin
from .models import StudentRequest, RequestNote, MissingDocument

admin.site.register(StudentRequest)
admin.site.register(RequestNote)
admin.site.register(MissingDocument)