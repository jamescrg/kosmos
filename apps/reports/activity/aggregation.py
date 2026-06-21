"""Shared data aggregation for the Activity report.

`build_activity_context` is the single source of truth for both `activity_index`
and `activity_list`. It resolves the report's calendar year (Jan through the
current month for the current year; the full Jan–Dec for a past year),
aggregates `TimeEntry` rows per user per month for the inverted table (users as
rows, months as columns, total on the far right), and assembles `chart_payload`
— a JSON-safe dict consumed by the stacked bar chart via `json_script`. The year
is held in the session and stepped by the `activity_year` view.
"""

from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Sum

from apps.accounts.models import CustomUser
from apps.activity.time.models import TimeEntry

# Distinct matters charted before the rest roll up into "Other". Kept small: a
# stacked bar with many categories is hard to colour distinctly and to read.
TOP_MATTERS = 4


def resolve_year(session_year):
    """Clamp the session's stored year to (–∞, current year]. Returns
    (year, current_year)."""
    current_year = date.today().year
    try:
        year = int(session_year)
    except (TypeError, ValueError):
        year = current_year
    return min(year, current_year), current_year


def _months_for_year(year, current_year):
    """Calendar months to show: Jan through the current month for the current
    year, otherwise the full Jan–Dec for a past year."""
    last_month = date.today().month if year == current_year else 12
    months = []
    for m in range(1, last_month + 1):
        first = date(year, m, 1)
        months.append(
            {"date": first, "name": first.strftime("%b"), "year": year, "month": m}
        )
    return months


def _build_matter_series(months):
    """Per-month billable hours/fees grouped by matter, capped at TOP_MATTERS.

    Returns a list of series dicts aligned to `months`:
        [{"label": "Acme v. Roe", "hours": [...], "fees": [...]}, ..., {"label": "Other", ...}]
    Matters outside the top-N (ranked by total hours over the window) fold into
    a trailing "Other" bucket.
    """
    if not months:
        return []

    window_start = months[0]["date"].replace(day=1)
    window_end = months[-1]["date"].replace(day=1) + relativedelta(months=1)

    ranking = (
        TimeEntry.objects.filter(
            matter__billable=True,
            date__gte=window_start,
            date__lt=window_end,
        )
        .values("matter_id", "matter__name")
        .annotate(total=Sum("hours"))
        .order_by("-total")
    )

    top = list(ranking[:TOP_MATTERS])
    top_ids = [row["matter_id"] for row in top]
    has_other = ranking.count() > len(top)

    # Stable order: top matters first (by total hours), then Other.
    series = [
        {
            "matter_id": row["matter_id"],
            "label": row["matter__name"] or "(no name)",
            "hours": [],
            "fees": [],
        }
        for row in top
    ]
    other = {"hours": [], "fees": []} if has_other else None

    for month_info in months:
        grouped = (
            TimeEntry.objects.filter(
                matter__billable=True,
                date__year=month_info["year"],
                date__month=month_info["month"],
            )
            .values("matter_id")
            .annotate(
                hours_sum=Sum("hours"),
                fees_sum=Sum(F("hours") * F("rate")),
            )
        )
        by_matter = {row["matter_id"]: row for row in grouped}

        other_hours = Decimal(0)
        other_fees = Decimal(0)
        for row in grouped:
            if row["matter_id"] not in top_ids:
                other_hours += row["hours_sum"] or 0
                other_fees += row["fees_sum"] or Decimal(0)

        for s in series:
            row = by_matter.get(s["matter_id"])
            s["hours"].append(float(row["hours_sum"] or 0) if row else 0.0)
            s["fees"].append(round(float(row["fees_sum"] or 0), 2) if row else 0.0)

        if other is not None:
            other["hours"].append(float(other_hours))
            other["fees"].append(round(float(other_fees), 2))

    result = [
        {"label": s["label"], "hours": s["hours"], "fees": s["fees"]} for s in series
    ]
    if other is not None:
        result.append(
            {"label": "Other", "hours": other["hours"], "fees": other["fees"]}
        )
    return result


def build_activity_context(request):
    """Full template context for the activity report, including `chart_payload`."""
    year, current_year = resolve_year(request.session.get("activity_year"))
    months = _months_for_year(year, current_year)

    # Years that actually have time entries, oldest first, for the year dropdown.
    available_years = sorted({d.year for d in TimeEntry.objects.dates("date", "year")})

    user_rows = []
    user_series = []  # chart datasets, aligned to `months`
    month_totals = [{"hours": 0, "fees": Decimal(0)} for _ in months]
    grand_total_hours = 0
    grand_total_fees = Decimal(0)

    def add_row(label, entries):
        """Aggregate `entries` per month into a table row + chart series, folding
        the contribution into the month and grand totals. Skips rows with no
        entries (returns without appending)."""
        nonlocal grand_total_hours, grand_total_fees
        cells = []
        hours_series = []
        fees_series = []
        row_hours = 0
        row_fees = Decimal(0)
        any_entries = False

        for idx, month_info in enumerate(months):
            agg = entries.filter(
                date__year=year,
                date__month=month_info["month"],
            ).aggregate(
                hours_sum=Sum("hours"),
                fees_sum=Sum(F("hours") * F("rate")),
                count=Count("id"),
            )
            hours = agg["hours_sum"] or 0
            fees = agg["fees_sum"] or Decimal(0)
            count = agg["count"] or 0
            any_entries = any_entries or count > 0

            cells.append({"hours": hours, "fees": fees, "entries_count": count})
            hours_series.append(float(hours))
            fees_series.append(round(float(fees), 2))
            row_hours += hours
            row_fees += fees
            month_totals[idx]["hours"] += hours
            month_totals[idx]["fees"] += fees

        if not any_entries:
            return

        user_rows.append(
            {
                "label": label,
                "cells": cells,
                "total_hours": row_hours,
                "total_fees": row_fees,
            }
        )
        user_series.append({"label": label, "hours": hours_series, "fees": fees_series})
        grand_total_hours += row_hours
        grand_total_fees += row_fees

    # Each active user is its own row, alphabetical.
    active_users = (
        CustomUser.objects.filter(timeentry__date__year=year, is_active=True)
        .distinct()
        .order_by("first_name", "last_name")
    )
    for user in active_users:
        label = f"{user.first_name} {user.last_name}".strip() or user.get_username()
        add_row(label, TimeEntry.objects.filter(user=user, matter__billable=True))

    # Inactive users are included, but rolled up into a single "Inactive" row.
    add_row(
        "Inactive",
        TimeEntry.objects.filter(user__is_active=False, matter__billable=True),
    )

    chart_payload = {
        "months": [m["name"] for m in months],
        "series": {
            "user": user_series,
            "matter": _build_matter_series(months),
        },
    }

    return {
        "app": "reports",
        "subapp": "activity",
        "months": months,
        "user_rows": user_rows,
        "month_totals": month_totals,
        "grand_total_hours": grand_total_hours,
        "grand_total_fees": grand_total_fees,
        "selected_year": year,
        "available_years": available_years,
        "chart_payload": chart_payload,
    }
