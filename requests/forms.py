from django import forms
from .models import StudentRequest, Student, Attachment


class StudentRequestForm(forms.ModelForm):
    class Meta:
        model = StudentRequest
        fields = ["student", "course_name", "request_type", "description"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-control"}),
            "course_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Intro to Computer Science"}),
            "request_type": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Leave Request, Extension Request"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe your request..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.all().order_by("name")
