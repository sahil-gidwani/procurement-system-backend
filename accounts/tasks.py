from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_password_reset_email(user_email, password_reset_url):
    send_mail(
        subject="Password Reset Request",
        message=f"Click the link to reset your password: {password_reset_url}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=True,
    )
    return "Password reset email sent"


@shared_task
def send_password_reset_confirm_email(user_email):
    send_mail(
        subject="Password Reset Confirmation",
        message="Your password has been reset successfully.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=True,
    )
    return "Password reset confirmation email sent"


@shared_task
def send_register_email(user_email):
    send_mail(
        subject = 'Welcome to Our Platform',
        message = 'Thank you for registering with us.',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=True,
    )
    return "Registration confirmation email sent"
