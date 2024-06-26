from django.db import models
from django.core.validators import MinValueValidator
from inventory.models import Inventory
from accounts.models import User


class PurchaseRequisition(models.Model):
    requisition_number = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    quantity_requested = models.IntegerField(validators=[MinValueValidator(1)])
    expected_delivery_date = models.DateField()
    URGENCY_LEVEL_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]
    urgency_level = models.CharField(
        max_length=10, choices=URGENCY_LEVEL_CHOICES, default="low"
    )
    comments = models.TextField(null=True, blank=True)
    attachments = models.ImageField(
        upload_to="requisition/attachments", null=True, blank=True
    )
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    report = models.FileField(upload_to="requisition/reports", null=True, blank=True)
    inventory = models.OneToOneField(Inventory, on_delete=models.CASCADE)

    def __str__(self):
        return self.requisition_number


class SupplierBid(models.Model):
    quantity_fulfilled = models.IntegerField()
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)]
    )
    date_submitted = models.DateTimeField(auto_now_add=True)
    days_delivery = models.IntegerField(validators=[MinValueValidator(1)])
    attachments = models.ImageField(upload_to="bid", null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="submitted"
    )
    supplier = models.ForeignKey(User, on_delete=models.CASCADE)
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["supplier", "requisition"]

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.supplier.username}"


class PurchaseOrder(models.Model):
    order_number = models.CharField(max_length=255)
    date_ordered = models.DateField(auto_now_add=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    bid = models.OneToOneField(SupplierBid, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_number
