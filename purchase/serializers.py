from rest_framework import serializers
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        exclude = ['status', 'inventory']


class SupplierBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBid
        exclude = ['status', 'requisition']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        exclude = ['status', 'bid']
