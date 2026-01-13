from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import StudentRequest, RequestNote, MissingDocument


@login_required
def request_list(request):
    if not request.user.is_staff:
        return redirect("/admin/")

    requests = StudentRequest.objects.all().order_by("-created_at")
    return render(request, "staff/request_list.html", {"requests": requests})


@login_required
def request_detail(request, request_id):
    if not request.user.is_staff:
        return redirect("/admin/")

    req = get_object_or_404(StudentRequest, id=request_id)
    notes = req.notes.all().order_by("-created_at")
    missing_docs = req.missing_docs.all().order_by("-created_at")

    return render(request, "staff/request_detail.html", {
        "req": req,
        "notes": notes,
        "missing_docs": missing_docs,
    })


@login_required
def add_note(request, request_id):
    if not request.user.is_staff:
        return redirect("/admin/")

    req = get_object_or_404(StudentRequest, id=request_id)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            RequestNote.objects.create(request=req, staff=request.user, text=text)
            messages.success(request, "✅ Note added successfully.")
        else:
            messages.error(request, "❌ Please write a note first.")

    return redirect("staff:request_detail", request_id=req.id)


@login_required
def request_docs(request, request_id):
    if not request.user.is_staff:
        return redirect("/admin/")

    req = get_object_or_404(StudentRequest, id=request_id)

    if request.method == "POST":
        doc_name = request.POST.get("doc_name", "").strip()
        instructions = request.POST.get("instructions", "").strip()

        if doc_name:
            MissingDocument.objects.create(
                request=req,
                doc_name=doc_name,
                instructions=instructions
            )
            req.status = "NEED_MORE_DOCS"
            req.save(update_fields=["status"])
            messages.success(request, "📎 Additional documents request sent.")
        else:
            messages.error(request, "❌ Please enter the missing document name.")

    return redirect("staff:request_detail", request_id=req.id)


@login_required
def send_to_hod(request, request_id):
    if not request.user.is_staff:
        return redirect("/admin/")

    req = get_object_or_404(StudentRequest, id=request_id)

    if req.missing_docs.filter(resolved=False).exists():
        messages.error(request, "❌ Cannot send: there are pending missing documents.")
        return redirect("staff:request_detail", request_id=req.id)

    req.status = "SENT_TO_HOD"
    req.save(update_fields=["status"])
    messages.success(request, "📨 Request sent to the Head of Department.")
    return redirect("staff:request_detail", request_id=req.id)


@login_required
def resolve_doc(request, doc_id):
    if not request.user.is_staff:
        return redirect("/admin/")

    doc = get_object_or_404(MissingDocument, id=doc_id)
    doc.resolved = True
    doc.save(update_fields=["resolved"])
    messages.success(request, "✅ Document marked as received.")
    return redirect("staff:request_detail", request_id=doc.request.id)