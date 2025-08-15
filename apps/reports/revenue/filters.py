import django_filters

from apps.invoicing.payments.models import Payment


class RevenueReportFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ["date_from", "date_to"]
