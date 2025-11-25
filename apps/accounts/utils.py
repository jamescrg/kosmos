import random
import string

from django.core.mail import send_mail


def generate_verification_code():
    """Generate a random 6-digit verification code."""
    return "".join(random.choices(string.digits, k=6))


def send_verification_email(user, code):
    """Send verification code to user's email."""
    send_mail(
        subject="Your Login Verification Code",
        message=f"Your verification code is: {code}\n\nThis code expires in 5 minutes.",
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )
