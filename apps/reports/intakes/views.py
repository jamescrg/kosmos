import os
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.management.filter_manager import FilterManager

from .aggregation import build_intakes_context
from .filters import IntakeReportFilter
from .functions import generate_intakes_pdf


@login_required
@staff_member_required
def intakes_index(request):
    return render(request, "reports/intakes/main.html", build_intakes_context(request))


@login_required
@staff_member_required
def intakes_list(request):
    return render(request, "reports/intakes/list.html", build_intakes_context(request))


@login_required
@staff_member_required
def intakes_filter(request):
    filter_manager = FilterManager(request, IntakeReportFilter, "intakes_filter")

    if filter_manager.process_filter():
        return HttpResponse(status=204, headers={"HX-Trigger": "intakesChanged"})

    # Get current filter data from session for display
    filter_data = request.session.get("intakes_filter", {})

    return render(request, "reports/intakes/filter.html", {"filter_data": filter_data})


@login_required
@staff_member_required
def intakes_pdf(request):
    """Export intakes report as PDF"""

    # Get filter data from session
    filter_data = request.session.get("intakes_filter", {})

    # Set date filter objects (None means no date filtering)
    date_from_obj = None
    date_to_obj = None
    date_from = filter_data.get("date_from")
    date_to = filter_data.get("date_to")

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            date_from = None

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            date_to = None

    # Generate PDF
    pdf_file = generate_intakes_pdf(date_from_obj, date_to_obj, request)

    # Create response
    with open(pdf_file.name, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/pdf")

    # Set filename for download
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"Intakes_Report_{current_date}.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # Clean up temporary file
    os.unlink(pdf_file.name)

    return response
