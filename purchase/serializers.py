from rest_framework import serializers
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        exclude = ['status', 'inventory']


class PurchaseRequisitionVendorSerializer(serializers.ModelSerializer):
    procurement_officer = serializers.StringRelatedField(source='inventory.procurement_officer')

    class Meta:
        model = PurchaseRequisition
        exclude = ['status', 'inventory']


class SupplierBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBid
        exclude = ['status', 'requisition', 'supplier']


class SupplierBidProcurementOfficerSerializer(serializers.ModelSerializer):
    supplier_rating = serializers.SerializerMethodField()
    class Meta:
        model = SupplierBid
        exclude = ['requisition']

    def get_supplier_rating(self, instance) -> float:
        return instance.supplier.vendor.vendor_rating


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        exclude = ['status', 'bid']
