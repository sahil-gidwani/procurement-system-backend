from rest_framework import serializers
from .models import InventoryReceipt, Invoice


class InventoryReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReceipt
        read_only_fields = ["inspection_report"]
        exclude = ["order"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        read_only_fields = ["payment_status", "invoice_report", "vendor_rated"]
        exclude = ["order"]


class InvoicePaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["payment_status"]


class InvoiceVendorRatingSerializer(serializers.ModelSerializer):
    vendor_rating = serializers.FloatField(min_value=0.00, max_value=5.00, required=True)
    class Meta:
        model = Invoice
        fields = ["vendor_rating", "vendor_rated"]
        read_only_fields = ["vendor_rated"]
