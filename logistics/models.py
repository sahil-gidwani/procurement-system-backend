from django.db import models
from django.core.validators import MinValueValidator
from purchase.models import PurchaseOrder


class InventoryReceipt(models.Model):
    CONDITION_CHOICES = [
        ("good", "Good"),
        ("damaged", "Damaged"),
        ("defective", "Defective"),
    ]

    receipt_id = models.CharField(max_length=255)
    receipt_date = models.DateField(auto_now_add=True)
    received_quantity = models.IntegerField(validators=[MinValueValidator(0)])
    received_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, null=True, blank=True)
    inspection_notes = models.TextField(null=True, blank=True)
    inspection_report = models.FileField(upload_to="inspection/reports", null=True, blank=True)
    order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.receipt_id} - {self.order.order_number}"


class Invoice(models.Model):
    PAYMENT_MODE_CHOICES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
        ("cash", "Cash"),
        ("cheque", "Cheque"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("paid", "Paid"),
        ("pending", "Pending"),
    ]

    invoice_number = models.CharField(max_length=255)
    invoice_date = models.DateField(auto_now_add=True)
    account_number = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    payment_due_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    invoice_report = models.FileField(upload_to="invoice/reports", null=True, blank=True)
    vendor_rated = models.BooleanField(default=False)
    order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.invoice_number} - {self.order.order_number}"
