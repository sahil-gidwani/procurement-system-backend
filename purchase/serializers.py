from rest_framework import serializers
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        fields = '__all__'
        exclude = ['status', 'inventory']


class SupplierBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBid
        fields = '__all__'
        exclude = ['status', 'requisition']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        exclude = ['status', 'bid']
