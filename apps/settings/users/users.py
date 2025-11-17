from django.core.paginator import Paginator

from apps.settings.users.filters import UserFilter

# Default filter settings for user list
DEFAULT_USER_FILTER = {"is_active": "True"}


def get_user_list(request):
    filter_data = request.session.get("user_filter", {})

    if filter_data:
        users = UserFilter(filter_data).qs
    else:
        # Apply default filter
        users = UserFilter(DEFAULT_USER_FILTER).qs

    page = request.GET.get("page")
    pagination = Paginator(users, 10).get_page(page)

    context = {
        "subapp": "users",
        "users": pagination.object_list,
        "pagination": pagination,
    }

    return context
