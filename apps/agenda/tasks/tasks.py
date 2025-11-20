from datetime import date, timedelta

from apps.accounts.models import CustomUser
from apps.agenda.tasks.filter import TasksFilter
from apps.agenda.tasks.models import Task
from apps.management.pagination import CustomPaginator
from apps.matters.models import Matter


def get_upcoming_tasks(request):
    """Get tasks due in the next 3 days (today + 2 days) for all users"""
    today = date.today()
    end_date = today + timedelta(days=2)

    # Query tasks due in the next 3 days - show ALL users' tasks
    upcoming = Task.objects.filter(
        date_due__gte=today, date_due__lte=end_date, status="Pending"
    )

    # Order by due date, then priority
    upcoming = upcoming.order_by("date_due", "priority")

    return upcoming


def get_list_data(request):
    list_data = {}

    today = date.today()

    filter_data = request.session.get("tasks_filter", {})

    if filter_data:
        filter_data = {
            **filter_data,
            "status": filter_data.get("status", "Pending"),
            "order_by": filter_data.get("order_by", "priority"),
        }

        filter = TasksFilter(filter_data)
        tasks = filter.qs

        user_id = filter_data.get("user")
        user_id = int(user_id) if user_id not in (None, "") else None

        matter_id = filter_data.get("matter")
        matter_id = int(matter_id) if matter_id not in (None, "") else None

        focus = filter_data.get("focus")

    else:
        default_filter = {
            "status": "Pending",
            "matter": None,
            "order_by": "priority",
            "user": request.user.id,
            "focus": "",
        }

        filter = TasksFilter(default_filter)
        tasks = filter.qs

        user_id = request.user.id
        matter_id = None
        focus = ""

    # Exclude upcoming tasks from main list if they're being shown separately
    show_upcoming_tasks = request.session.get("show_upcoming_tasks", True)
    if show_upcoming_tasks:
        upcoming_tasks = get_upcoming_tasks(request)
        upcoming_ids = list(upcoming_tasks.values_list("id", flat=True))
        if upcoming_ids:
            tasks = tasks.exclude(id__in=upcoming_ids)

    pagination = CustomPaginator(
        tasks, per_page=20, request=request, session_key="tasks_pagination"
    )

    selected_matter = None
    if matter_id:
        selected_matter = Matter.objects.filter(id=matter_id).first()

    selected_user = None
    if user_id:
        selected_user = CustomUser.objects.filter(id=user_id).first()

    list_data = {
        "pagination": pagination,
        "session_key": "tasks_pagination",
        "trigger_key": "tasksListChanged",
        "objects": pagination.get_object_list(),
        "matters": Matter.objects.filter(status__in=["Pending", "Open"]).order_by(
            "name"
        ),
        "today": today,
        "users": CustomUser.objects.filter(is_active=True).order_by("username"),
        "user_id": user_id,
        "matter_id": matter_id,
        "selected_matter": selected_matter.name if selected_matter else None,
        "selected_user": selected_user.username.capitalize() if selected_user else None,
        "focus": focus,
        "filter_label": filter_data.get("filter_label", None) if filter_data else None,
    }

    return list_data
