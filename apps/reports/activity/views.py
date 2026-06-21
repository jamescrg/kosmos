from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .aggregation import build_activity_context, resolve_end


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
def activity_period(request):
    """Step the rolling window's end month (held in the session) one month back
    or forward, capped at the current month, then re-render the report."""
    end, current_first = resolve_end(request.session.get("activity_end"))

    direction = request.POST.get("direction")
    if direction == "prev":
        end = end - relativedelta(months=1)
    elif direction == "next":
        end = min(end + relativedelta(months=1), current_first)

    request.session["activity_end"] = end.strftime("%Y-%m")
    request.session.modified = True
    return HttpResponse(status=204, headers={"HX-Trigger": "activityChanged"})
