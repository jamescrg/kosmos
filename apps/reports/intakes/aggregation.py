"""Intakes report context — shared by the index/list views.

Builds the existing per-month practice-area and status tables plus three chart
payloads: a month-over-month volume bar, a practice-area donut, and an outcomes
(conversion) donut. Defaults to a rolling 6-month window (like the other
reports) so the month-over-month chart is meaningful out of the box; the date
filter still overrides it.
"""

from collections import defaultdict
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Count
from django.db.models.functions import TruncMonth

from apps.intakes.models import Intake

# Practice areas / statuses to match the intake form choices.
PRACTICE_AREAS = [
    "General",
    "Boundary",
    "Title",
    "LLT - LL",
    "LLT - T",
    "QT",
    "HOA",
    "Fraud",
    "Construction",
]
INTAKE_STATUSES = [
    "Open",
    "Pending",
    "Accepted",
    "Referred Out",
    "Client Declined",
    "Unresponsive",
]
# The status that represents a converted intake (signed client / accepted work).
CONVERTED_STATUS = "Accepted"


def _parse(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def build_intakes_context(request):
    filter_data = request.session.get("intakes_filter", {})
    date_from = filter_data.get("date_from")
    date_to = filter_data.get("date_to")
    date_from_obj = _parse(date_from)
    date_to_obj = _parse(date_to)

    # Default to a rolling 6 months (first of the month, 5 months back).
    if not date_from_obj and not date_to_obj:
        date_from_obj = date.today().replace(day=1) - relativedelta(months=5)
        date_from = date_from_obj.strftime("%Y-%m-%d")

    intakes = Intake.objects.all()
    if date_from_obj:
        intakes = intakes.filter(date__gte=date_from_obj)
    if date_to_obj:
        intakes = intakes.filter(date__lte=date_to_obj)

    months = (
        intakes.annotate(month=TruncMonth("date"))
        .values("month")
        .distinct()
        .order_by("month")
    )

    # --- Per-month practice-area table ---
    intake_data = []
    totals_by_practice_area = defaultdict(int)
    for md in months:
        if not md["month"]:
            continue
        row = {
            "month": md["month"].strftime("%B %Y"),
            "month_sort": md["month"],
            "practice_areas": {},
            "total": 0,
        }
        for pa in PRACTICE_AREAS:
            count = intakes.filter(
                date__year=md["month"].year,
                date__month=md["month"].month,
                practice_area__name=pa,
            ).count()
            row["practice_areas"][pa] = count
            row["total"] += count
            totals_by_practice_area[pa] += count
        row["percentages"] = (
            {
                pa: round(row["practice_areas"][pa] / row["total"] * 100, 1)
                for pa in PRACTICE_AREAS
            }
            if row["total"]
            else {}
        )
        intake_data.append(row)

    total_intakes = sum(r["total"] for r in intake_data)
    percentages_by_practice_area = (
        {
            pa: round(totals_by_practice_area[pa] / total_intakes * 100, 1)
            for pa in PRACTICE_AREAS
        }
        if total_intakes
        else {}
    )

    # --- Per-month status table ---
    status_data = []
    totals_by_status = defaultdict(int)
    for md in months:
        if not md["month"]:
            continue
        row = {
            "month": md["month"].strftime("%B %Y"),
            "month_sort": md["month"],
            "statuses": {},
            "total": 0,
        }
        for st in INTAKE_STATUSES:
            count = intakes.filter(
                date__year=md["month"].year,
                date__month=md["month"].month,
                status=st,
            ).count()
            row["statuses"][st] = count
            row["total"] += count
            totals_by_status[st] += count
        row["percentages"] = (
            {
                st: round(row["statuses"][st] / row["total"] * 100, 1)
                for st in INTAKE_STATUSES
            }
            if row["total"]
            else {}
        )
        status_data.append(row)

    percentages_by_status = (
        {
            st: round(totals_by_status[st] / total_intakes * 100, 1)
            for st in INTAKE_STATUSES
        }
        if total_intakes
        else {}
    )

    # --- Charts ---
    # Month-over-month volume (true totals: every intake with a date in range).
    monthly = list(
        intakes.exclude(date=None)
        .annotate(m=TruncMonth("date"))
        .values("m")
        .annotate(c=Count("id"))
        .order_by("m")
    )
    flow_counts = [r["c"] for r in monthly]
    flow_chart = {
        "months": [r["m"].strftime("%b ’%y") for r in monthly],
        "series": {"flow": [{"label": "Intakes", "count": flow_counts}]},
        "top_labels": [str(c) for c in flow_counts],
    }

    # Practice-area distribution (no practice area -> trailing grey "Unspecified").
    pa_rows = list(intakes.values("practice_area__name").annotate(c=Count("id")))
    named = sorted(
        (r for r in pa_rows if r["practice_area__name"]), key=lambda r: -r["c"]
    )
    unspecified = sum(r["c"] for r in pa_rows if not r["practice_area__name"])
    pa_labels = [r["practice_area__name"] for r in named]
    pa_counts = [r["c"] for r in named]
    if unspecified:
        pa_labels.append("Unspecified")
        pa_counts.append(unspecified)
    practice_donut = {
        "labels": pa_labels,
        "count": pa_counts,
        "hasOther": bool(unspecified),
    }

    # Outcomes / conversion, ordered by the canonical status list (present only).
    st_counts = {
        r["status"]: r["c"] for r in intakes.values("status").annotate(c=Count("id"))
    }
    conv_labels = [s for s in INTAKE_STATUSES if st_counts.get(s)]
    conv_labels += [s for s in st_counts if s not in INTAKE_STATUSES and st_counts[s]]
    conversion_donut = {
        "labels": conv_labels,
        "count": [st_counts[s] for s in conv_labels],
    }
    total_all = sum(st_counts.values())
    converted_count = st_counts.get(CONVERTED_STATUS, 0)
    conversion_rate = round(converted_count / total_all * 100, 1) if total_all else 0

    return {
        "app": "reports",
        "subapp": "intakes",
        "intake_data": intake_data,
        "status_data": status_data,
        "total_intakes": total_intakes,
        "totals_by_practice_area": dict(totals_by_practice_area),
        "totals_by_status": dict(totals_by_status),
        "percentages_by_practice_area": percentages_by_practice_area,
        "percentages_by_status": percentages_by_status,
        "practice_areas": PRACTICE_AREAS,
        "intake_statuses": INTAKE_STATUSES,
        "date_from": date_from,
        "date_to": date_to,
        "flow_chart": flow_chart,
        "practice_donut": practice_donut,
        "conversion_donut": conversion_donut,
        "conversion_rate": conversion_rate,
        "converted_count": converted_count,
        "intakes_total_all": total_all,
    }
