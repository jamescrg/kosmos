from dateutil.relativedelta import relativedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.reports.activity.aggregation import resolve_end

from .aggregation import build_realization_context


@login_required
@staff_member_required
def realization_index(request):
    return render(
        request, "reports/realization/main.html", build_realization_context(request)
    )


@login_required
@staff_member_required
def realization_list(request):
    return render(
        request, "reports/realization/list.html", build_realization_context(request)
    )


@login_required
@staff_member_required
def realization_period(request):
    """Step the rolling window's end month (held in the session) one month back
    or forward, capped at the current month, then re-render the report."""
    end, current_first = resolve_end(request.session.get("realization_end"))

    direction = request.POST.get("direction")
    if direction == "prev":
        end = end - relativedelta(months=1)
    elif direction == "next":
        end = min(end + relativedelta(months=1), current_first)

    request.session["realization_end"] = end.strftime("%Y-%m")
    request.session.modified = True
    return HttpResponse(status=204, headers={"HX-Trigger": "realizationChanged"})
