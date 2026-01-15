from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import StudentRequest, Attachment
from .forms import StudentRequestForm

def dashboard(request):
    selected_status = request.GET.get("status", "")
    selected_type = request.GET.get("type", "")
    qs = StudentRequest.objects.select_related("student").prefetch_related("attachments").order_by("-submitted_at")

    if selected_status:
        qs = qs.filter(status=selected_status)
    if selected_type:
        qs = qs.filter(request_type=selected_type)

    request_types = StudentRequest.objects.values_list("request_type", flat=True).distinct().order_by("request_type")

    return render(request, "requests/dashboard.html", {
        "requests": qs,
        "request_types": request_types,
        "selected_status": selected_status,
        "selected_type": selected_type,
    })

def request_detail_partial(request, pk):
    r = get_object_or_404(StudentRequest.objects.select_related("student").prefetch_related("attachments"), pk=pk)
    return render(request, "requests/request_detail_partial.html", {"r": r})

@require_POST
def update_status(request, pk):
    r = get_object_or_404(StudentRequest, pk=pk)
    status = request.POST.get("status", "").strip()
    feedback = request.POST.get("feedback", "").strip()

    if status not in {"approved", "rejected", "needs_info", "pending"}:
        return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

    r.status = status
    r.lecturer_feedback = feedback
    r.save()
    return JsonResponse({"success": True})


def create_request(request):
    if request.method == "POST":
        form = StudentRequestForm(request.POST, request.FILES)
        if form.is_valid():
            # Generate unique request_id
            import random
            import string
            while True:
                request_id = f"REQ-{''.join(random.choices(string.digits, k=6))}"
                if not StudentRequest.objects.filter(request_id=request_id).exists():
                    break
            
            student_request = form.save(commit=False)
            student_request.request_id = request_id
            student_request.save()
            
            # Handle multiple file uploads
            files = request.FILES.getlist("attachments")
            for file in files:
                Attachment.objects.create(request=student_request, file=file)
            
            messages.success(request, f"Request {request_id} submitted successfully!")
            return redirect("dashboard")
    else:
        form = StudentRequestForm()
    
    return render(request, "requests/create_request.html", {"form": form})
