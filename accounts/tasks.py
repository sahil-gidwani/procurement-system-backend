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
        fail_silently=False,
    )
