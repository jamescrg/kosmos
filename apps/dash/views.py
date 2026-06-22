from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render

from apps.accounts.access import filter_matters_for_user
from apps.activity.expenses.models import ExpenseEntry
from apps.activity.time.models import TimeEntry
from apps.calendar.models import Event
from apps.intakes.models import Intake
from apps.invoicing.credits.models import Credit
from apps.invoicing.invoices.models import Invoice
from apps.invoicing.payments.models import Payment
from apps.matters.models import Matter
from apps.reports.wip.aggregation import (
    WIP_PERIODS,
    wip_matter_breakdown,
    wip_period_range,
    wip_user_breakdown,
    wip_user_matters,
)
from apps.trust.trust import get_confirmed_client_balance


def _nth_working_day(start, count):
    """Date of the `count`-th working day (Mon–Fri) on or after `start`."""
    day = start
    seen = 0
    while True:
        if day.weekday() < 5:
            seen += 1
            if seen == count:
                return day
        day += timedelta(days=1)


def dash_wip_context(request):
    """Context for the dash 'Unbilled Time' section, filtered by the session
    quick-period. Admins (reporting access) get by-user + by-matter breakdowns
    toggled client-side; everyone else gets only their own WIP. `?view=user`
    lets a privileged user preview the regular-user view."""
    period = request.session.get("dash_wip_period", "this_month")
    if period not in dict(WIP_PERIODS):
        period = "this_month"
    date_min, date_max = wip_period_range(period)
    preview_user = request.GET.get("view") == "user"
    wip_show_all = (
        request.user.is_admin or request.user.perm_reports
    ) and not preview_user

    ctx = {
        "wip_show_all": wip_show_all,
        "wip_period": period,
        "wip_period_label": dict(WIP_PERIODS).get(period, "All Dates"),
        "wip_periods": WIP_PERIODS,
        "wip_preview_user": preview_user,
        "user_rows": None,
        "user_donut": None,
        "matter_rows": None,
        "matter_donut": None,
        "user_self_matters": None,
        "user_self_donut": None,
    }
    if wip_show_all:
        ctx["user_rows"], ctx["user_donut"], totals = wip_user_breakdown(
            date_min=date_min, date_max=date_max
        )
        ctx["matter_rows"], ctx["matter_donut"], _ = wip_matter_breakdown(
            top_n=5, date_min=date_min, date_max=date_max
        )
    else:
        ctx["user_self_matters"], ctx["user_self_donut"], totals = wip_user_matters(
            request.user, top_n=5, date_min=date_min, date_max=date_max
        )
    ctx["totals"] = totals
    return ctx


@login_required
def wip_section(request):
    """Render just the dash 'Unbilled Time' section (reloaded on period change)."""
    return render(request, "dash/wip_section.html", dash_wip_context(request))


@login_required
def set_wip_period(request, period):
    """Store the dash WIP quick-period and trigger a section reload."""
    request.session["dash_wip_period"] = period
    request.session.modified = True
    return HttpResponse(status=204, headers={"HX-Trigger": "wipChanged"})


@login_required
def dash_index(request):
    today = date.today()

    # Upcoming events: pending events from today through the 3rd working day
    # (weekends in between still show). The table is hidden when empty.
    window_end = _nth_working_day(today, 3)
    upcoming_events = Event.objects.filter(
        status="Pending", date__gte=today, date__lte=window_end
    ).order_by("date", "start_time", "party")

    # Matters with low clearance (< $1000)
    # Use subqueries to calculate unbilled amounts
    unbilled_fees_subquery = (
        TimeEntry.objects.filter(
            matter=OuterRef("pk"),
            entered=False,
            invoice__isnull=True,
        )
        .exclude(comp=True)
        .values("matter")
        .annotate(total=Sum(F("hours") * F("rate")))
        .values("total")
    )

    unbilled_expenses_subquery = (
        ExpenseEntry.objects.filter(
            matter=OuterRef("pk"),
            entered=False,
            invoice__isnull=True,
        )
        .exclude(comp=True)
        .values("matter")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    # Get matters with unbilled activity
    matters_with_unbilled = (
        filter_matters_for_user(
            Matter.objects.filter(status="Open", billable=True), request.user
        )
        .annotate(
            unbilled_fees=Coalesce(
                Subquery(unbilled_fees_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            unbilled_expenses=Coalesce(
                Subquery(unbilled_expenses_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
        )
        .filter(Q(unbilled_fees__gt=0) | Q(unbilled_expenses__gt=0))
    )

    # Convert to list and calculate clearance
    low_clearance_matters = []
    client_trust_balances = {}

    for matter in matters_with_unbilled:
        # Get trust balance for this matter's client (cached by client)
        if matter.client:
            if matter.client.id not in client_trust_balances:
                try:
                    client_trust_balances[matter.client.id] = (
                        get_confirmed_client_balance(matter.client.id)
                    )
                except Exception:
                    client_trust_balances[matter.client.id] = 0

            trust_balance = client_trust_balances[matter.client.id]
            total_activity = matter.unbilled_fees + matter.unbilled_expenses

            # Calculate clearance (only if there's a trust balance)
            if trust_balance > 0:
                clearance = trust_balance - total_activity
                if clearance < 1000:
                    matter.clearance = clearance
                    matter.trust_balance = trust_balance
                    matter.total_activity = total_activity
                    low_clearance_matters.append(matter)

    # Sort by clearance ascending (lowest first)
    low_clearance_matters.sort(key=lambda m: m.clearance)
    low_clearance_matters = low_clearance_matters[:10]

    # Matters with outstanding balance due (excluding deferred)
    # Use subqueries to calculate at database level (avoid N+1)

    # Subquery for invoice fees (excluding comp'd entries)
    invoice_fees_subquery = (
        TimeEntry.objects.filter(invoice=OuterRef("pk"))
        .exclude(comp=True)
        .values("invoice")
        .annotate(total=Sum(F("hours") * F("rate"), output_field=DecimalField()))
        .values("total")
    )

    # Subquery for invoice expenses (excluding comp'd entries)
    invoice_expenses_subquery = (
        ExpenseEntry.objects.filter(invoice=OuterRef("pk"))
        .exclude(comp=True)
        .values("invoice")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    # Annotate invoices with their final_total
    invoices_with_totals = Invoice.objects.annotate(
        net_fees=Coalesce(
            Subquery(invoice_fees_subquery, output_field=DecimalField()), 0
        ),
        net_expenses=Coalesce(
            Subquery(invoice_expenses_subquery, output_field=DecimalField()), 0
        ),
        final_total=ExpressionWrapper(
            F("net_fees") + F("net_expenses") - F("discount"),
            output_field=DecimalField(),
        ),
    )

    # Subquery for total billed (all invoices except DRAFT/APPROVED)
    billed_subquery = (
        invoices_with_totals.filter(matter=OuterRef("pk"))
        .exclude(status__in=["DRAFT", "APPROVED", "VOID"])
        .values("matter")
        .annotate(total=Sum("final_total"))
        .values("total")
    )

    # Subquery for deferred invoice totals
    deferred_subquery = (
        invoices_with_totals.filter(matter=OuterRef("pk"), status="DEFERRED")
        .values("matter")
        .annotate(total=Sum("final_total"))
        .values("total")
    )

    # Subquery for total payments
    paid_subquery = (
        Payment.objects.filter(matter=OuterRef("pk"))
        .values("matter")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    # Subquery for total credits
    credits_subquery = (
        Credit.objects.filter(matter=OuterRef("pk"))
        .values("matter")
        .annotate(total=Sum("amount"))
        .values("total")
    )

    # Annotate matters and filter for positive balance due
    balance_due_matters = list(
        filter_matters_for_user(Matter.objects.filter(billable=True), request.user)
        .annotate(
            billed=Coalesce(
                Subquery(billed_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            deferred=Coalesce(
                Subquery(deferred_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            paid=Coalesce(
                Subquery(paid_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            credits=Coalesce(
                Subquery(credits_subquery, output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
            balance_due=ExpressionWrapper(
                F("billed") - F("paid") - F("deferred") - F("credits"),
                output_field=DecimalField(),
            ),
        )
        .filter(balance_due__gt=0)
        .order_by("-balance_due")[:10]
    )

    # Open intakes
    open_intakes = Intake.objects.filter(status="Open").order_by("-date")[:10]

    context = {
        "app": "dash",
        "upcoming_events": upcoming_events,
        "low_clearance_matters": low_clearance_matters,
        "balance_due_matters": balance_due_matters,
        "open_intakes": open_intakes,
        "today": today,
        **dash_wip_context(request),
    }

    return render(request, "dash/dash.html", context)
