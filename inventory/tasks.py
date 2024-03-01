from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from .models import Inventory
from accounts.models import User


@shared_task
def send_inventory_notifications():
    # Get distinct procurement officers
    procurement_officers = Inventory.objects.values_list(
        "procurement_officer", flat=True
    ).distinct()

    # Iterate through procurement officers
    for officer_id in procurement_officers:
        officer_email = User.objects.get(id=officer_id).email
        item_names = Inventory.objects.filter(
            procurement_officer=officer_id
        ).values_list("item_name", flat=True)
        item_list = ", ".join(item_names)

        # Compose email
        subject = "Reminder: Update Inventory Items"
        message = f"Dear Procurement Officer,\n\nThis is a reminder to review and update the following inventory items assigned to you:\n\n{item_list}\n\nThank you."
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [officer_email],
            fail_silently=True,
        )

    return "Inventory notification emails sent successfully."
