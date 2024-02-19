from django.db import models
from inventory.models import Inventory


class PurchaseRequisition(models.Model):
    requisition_number = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    quantity_requested = models.IntegerField()
    expected_delivery_date = models.DateField()
    URGENCY_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]
    urgency_level = models.CharField(max_length=10, choices=URGENCY_LEVEL_CHOICES, default='low')
    comments = models.TextField(null=True, blank=True)
    attachments = models.ImageField(upload_to="requisition/attachments", null=True, blank=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    report = models.FileField(upload_to="requisition/reports", null=True, blank=True)
    inventory = models.OneToOneField(Inventory, on_delete=models.CASCADE)


class SupplierBid(models.Model):
    quantity_fulfilled = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_submitted = models.DateTimeField(auto_now_add=True)
    days_delivery = models.IntegerField()
    attachments = models.ImageField(upload_to="bid", null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE)


class PurchaseOrder(models.Model):
    order_number = models.CharField(max_length=255)
    date_ordered = models.DateField(auto_now_add=True)
    quantity_ordered = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bid = models.OneToOneField(SupplierBid, on_delete=models.CASCADE)
