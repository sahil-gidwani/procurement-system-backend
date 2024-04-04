from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import PurchaseRequisition, SupplierBid


@shared_task
def send_requisition_update_email(requisition_id):
    requisition = PurchaseRequisition.objects.get(id=requisition_id)

    # Get all vendors who submitted bids for the given requisition
    submitted_bids = SupplierBid.objects.filter(
        requisition_id=requisition_id
    ).select_related("supplier")

    # Extract unique email addresses of vendors
    vendor_emails = set(bid.supplier.email for bid in submitted_bids)

    subject = "Requisition Updated"
    message = f"Dear Vendor,\n\nRequisition ID {requisition.requisition_number} has been updated.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        vendor_emails,
        fail_silently=True,
    )
    return "Requisition update email sent successfully."


@shared_task
def send_supplier_bid_email(procurement_officer_email, supplier_name, requisition_id):
    subject = "New Supplier Bid"
    message = f"Dear Procurement Officer,\n\nA new bid has been submitted by {supplier_name} for requisition ID {requisition_id}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [procurement_officer_email],
        fail_silently=True,
    )
    return "Supplier bid email sent successfully."


@shared_task
def send_supplier_bid_update_email(
    procurement_officer_email, supplier_name, requisition_id
):
    subject = "Supplier Bid Update"
    message = f"Dear Procurement Officer,\n\n{supplier_name} has updated their bid for requisition ID {requisition_id}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [procurement_officer_email],
        fail_silently=True,
    )
    return "Supplier bid update email sent successfully."


@shared_task
def send_bid_accepted_email(vendor_email, bid_id, requisition_number):
    subject = "Bid Accepted"
    message = f"Dear Vendor,\n\nYour bid with bid ID {bid_id} has been accepted for requisition number {requisition_number}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [vendor_email],
        fail_silently=True,
    )
    return "Bid accepted email sent successfully."


@shared_task
def send_bid_rejected_email(vendor_email, bid_id, requisition_number):
    subject = "Bid Rejected"
    message = f"Dear Vendor,\n\nYour bid with bid ID {bid_id} has been rejected for requisition number {requisition_number}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        vendor_email,
        fail_silently=True,
    )
    return "Bid rejected email sent successfully."


@shared_task
def send_requisition_accepted_email(procurement_officer_email, requisition_id):
    subject = "Requisition Accepted"
    message = f"Dear Procurement Officer,\n\nRequisition ID {requisition_id} has been accepted.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [procurement_officer_email],
        fail_silently=True,
    )
    return "Requisition accepted email sent successfully."


@shared_task
def send_purchase_order_email(
    recepients, bid_id, requisition_id, purchase_order_number
):
    subject = "Purchase Order Created"
    message = f"Dear User,\n\nA purchase order with number {purchase_order_number} has been created for bid ID {bid_id} and requisition ID {requisition_id}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recepients,
        fail_silently=True,
    )
    return "Purchase order email sent successfully."


@shared_task
def send_purchase_order_status_email(
    procurement_officer_email, purchase_order_number, new_status
):
    subject = "Purchase Order Status Update"
    message = f"Dear Procurement Officer,\n\nThe status of purchase order number {purchase_order_number} has been updated to {new_status}.\n\nThank you."
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [procurement_officer_email],
        fail_silently=True,
    )
    return "Purchase order status email sent successfully."
