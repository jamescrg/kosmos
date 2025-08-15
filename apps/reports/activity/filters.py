import django_filters

from apps.activity.time.models import TimeEntry


class ActivityReportFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")
    exclude_inactive = django_filters.BooleanFilter(method="filter_exclude_inactive")

    class Meta:
        model = TimeEntry
        fields = ["date_from", "date_to", "exclude_inactive"]

    def filter_exclude_inactive(self, queryset, name, value):
        # This is handled in the view, just return the queryset
        return queryset
