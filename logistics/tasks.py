import os
from celery import shared_task
import cloudinary.uploader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.mail import send_mail
from .models import InventoryReceipt, Invoice


@shared_task
def generate_report_and_save(instance_id, report_type):
    if report_type == "inventory_receipt":
        instance = InventoryReceipt.objects.get(id=instance_id)
        filename = f"inventory_receipt_report_{instance.id}.pdf"
    elif report_type == "invoice":
        instance = Invoice.objects.get(id=instance_id)
        filename = f"invoice_report_{instance.id}.pdf"
    else:
        raise ValueError("Invalid report type")

    directory = os.path.join(settings.BASE_DIR, "logistics", "reports")
    file_path = os.path.join(directory, filename)

    try:
        # Create the directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Generate the PDF
        # TODO: Add logo and other details (e.g. company name, address, etc.)
        c = canvas.Canvas(file_path, pagesize=letter)
        if report_type == "inventory_receipt":
            c.drawString(100, 750, f"Inventory Receipt Report - {instance.receipt_id}")
            c.drawString(100, 730, f"Receipt Date: {instance.receipt_date}")
            c.drawString(100, 710, f"Received Quantity: {instance.received_quantity}")
            c.drawString(100, 690, f"Received Condition: {instance.received_condition}")
            c.drawString(100, 670, f"Inspection Notes: {instance.inspection_notes}")

        elif report_type == "invoice":
            c.drawString(100, 750, f"Invoice Report - {instance.invoice_number}")
            c.drawString(100, 730, f"Invoice Date: {instance.invoice_date}")
            c.drawString(100, 710, f"Account Number: {instance.account_number}")
            c.drawString(100, 690, f"Total Amount: {instance.total_amount}")
            c.drawString(100, 670, f"Payment Due Date: {instance.payment_due_date}")
            c.drawString(100, 650, f"Payment Mode: {instance.payment_mode}")
            c.drawString(100, 630, f"Payment Status: {instance.payment_status}")

        c.save()

        # Open the PDF file and read its content
        with open(file_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()

        # Save the content to the model's FileField
        # TODO: Find a solution to overwrite the existing file
        if report_type == "inventory_receipt":
            # Delete the existing report if it exists
            # if instance.inspection_report:
            #     cloudinary.uploader.destroy(instance.inspection_report.public_id)
            #     instance.inspection_report.delete()
            instance.inspection_report.save(
                filename, ContentFile(pdf_content), save=True
            )
        elif report_type == "invoice":
            # Delete the existing report if it exists
            # if instance.invoice_report:
            #     cloudinary.uploader.destroy(instance.invoice_report.public_id)
            #     instance.invoice_report.delete()
            instance.invoice_report.save(filename, ContentFile(pdf_content), save=True)

        # Clean up the file after uploading
        os.remove(file_path)

        return f"{report_type} Report generated and saved successfully."

    except Exception as e:
        return f"Error generating report: {e}"


@shared_task
def send_logistics_email(instance_id, type, action):
    if type == "inventory_receipt":
        instance = InventoryReceipt.objects.get(id=instance_id)
        if action not in ["created", "updated", "deleted"]:
            raise ValueError("Invalid action")
        subject = f"Inventory Receipt {action.capitalize()}"
        message = f"Dear User,\n\nThe inventory receipt with ID {instance.receipt_id} has been {action}.\n\nThank you."
    elif type == "invoice":
        instance = Invoice.objects.get(id=instance_id)
        if action not in [
            "created",
            "updated",
            "deleted",
            "payment_received",
            "vendor_rated",
        ]:
            raise ValueError("Invalid action")
        subject = f"Invoice {action.capitalize()}"
        message = f"Dear User,\n\nThe invoice with number {instance.invoice_number} has been {action}.\n\nThank you."
    else:
        raise ValueError("Invalid type")

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [
                instance.order.bid.requisition.inventory.procurement_officer.email,
                instance.order.bid.supplier.email,
            ],
            fail_silently=True,
        )
        return f"{type.capitalize()} {action} email sent successfully."
    except Exception as e:
        return f"Error sending email: {e}"
