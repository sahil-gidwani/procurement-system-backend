from rest_framework import serializers
from .models import InventoryReceipt, Invoice


class InventoryReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReceipt
        read_only_fields = ["inspection_report_url"]
        exclude = ["order"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        read_only_fields = ["payment_status", "invoice_report_url", "vendor_rated"]
        exclude = ["order"]
