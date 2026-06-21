from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .aggregation import build_activity_context


@login_required
@staff_member_required
def activity_index(request):
    return render(
        request, "reports/activity/main.html", build_activity_context(request)
    )


@login_required
@staff_member_required
def activity_list(request):
    return render(
        request, "reports/activity/list.html", build_activity_context(request)
    )


@login_required
@staff_member_required
def activity_year(request):
    """Set the report's calendar year (held in the session) from the year
    dropdown, capped at the current year, then re-render the report."""
    today = date.today()
    try:
        year = int(request.POST.get("year", today.year))
    except (TypeError, ValueError):
        year = today.year

    request.session["activity_year"] = min(year, today.year)
    request.session.modified = True
    return HttpResponse(status=204, headers={"HX-Trigger": "activityChanged"})
