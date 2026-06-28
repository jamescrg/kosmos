from django.urls import path

from apps.invoicing.pay.views import (
    balance_charge,
    balance_pay_page,
    pay_charge,
    pay_page,
    processor_webhook,
)

app_name = "pay"

urlpatterns = [
    # Public, tokenized — no login. The signed token carries the invoice uuid.
    path("pay/<str:token>/", pay_page, name="invoice"),
    path("pay/<str:token>/charge/", pay_charge, name="charge"),
    # Catch-up: pay a matter's full open balance (token carries the matter id).
    path("pay/balance/<str:token>/", balance_pay_page, name="balance"),
    path("pay/balance/<str:token>/charge/", balance_charge, name="balance-charge"),
    # Processor settlement/return notifications (verified by re-fetch).
    path("webhooks/<str:processor>/", processor_webhook, name="webhook"),
]
