"""
Toast notification utilities for HTMX responses.

Usage in views:
    from utils.toasts import toast_success, toast_error, add_toast

    def my_view(request):
        # Do something...
        response = HttpResponse(...)
        return toast_success(response, "Item saved successfully!")

    # Or with a title:
    def another_view(request):
        response = render(request, 'template.html')
        return toast_error(response, "Failed to save", title="Error")

    # Or add multiple toasts:
    def multi_toast_view(request):
        response = HttpResponse(...)
        add_toast(response, "success", "First message")
        add_toast(response, "info", "Second message")
        return response
"""

import json


def add_toast(response, toast_type, message, title=None, duration=None, link=None):
    """
    Add a toast notification to an HTMX response.

    Args:
        response: HttpResponse object
        toast_type: One of 'success', 'error', 'warning', 'info'
        message: Toast message text
        title: Optional title for the toast
        duration: Auto-dismiss duration in ms (0 = no auto-dismiss)
                  Defaults: success/warning/info = 5000ms, error = 0 (sticky)
        link: Optional dict with 'url' and 'text' for a link in the toast body

    Returns:
        The modified response object
    """
    toast_data = {
        "type": toast_type,
        "message": message,
    }

    if title:
        toast_data["title"] = title

    if duration is not None:
        toast_data["duration"] = duration

    if link:
        toast_data["link"] = link

    # Check if there are existing toasts
    existing = response.get("HX-Toasts")
    if existing:
        try:
            toasts = json.loads(existing)
            toasts.append(toast_data)
            response["HX-Toasts"] = json.dumps(toasts)
        except json.JSONDecodeError:
            response["HX-Toasts"] = json.dumps([toast_data])
    else:
        # First toast - use singular header
        response["HX-Toast"] = json.dumps(toast_data)

    return response


def toast_success(response, message, title=None, duration=5000, link=None):
    """Add a success toast to the response."""
    return add_toast(response, "success", message, title, duration, link)


def toast_error(response, message, title=None, duration=0):
    """Add an error toast to the response. Errors are sticky by default."""
    return add_toast(response, "error", message, title, duration)


def toast_warning(response, message, title=None, duration=5000):
    """Add a warning toast to the response."""
    return add_toast(response, "warning", message, title, duration)


def toast_info(response, message, title=None, duration=5000):
    """Add an info toast to the response."""
    return add_toast(response, "info", message, title, duration)


class ToastMixin:
    """
    Mixin for class-based views to easily add toast notifications.

    Usage:
        class MyView(ToastMixin, View):
            def post(self, request):
                # Do something...
                response = HttpResponse(...)
                return self.toast_success(response, "Saved!")
    """

    def toast_success(self, response, message, title=None, duration=5000):
        return toast_success(response, message, title, duration)

    def toast_error(self, response, message, title=None, duration=0):
        return toast_error(response, message, title, duration)

    def toast_warning(self, response, message, title=None, duration=5000):
        return toast_warning(response, message, title, duration)

    def toast_info(self, response, message, title=None, duration=5000):
        return toast_info(response, message, title, duration)
