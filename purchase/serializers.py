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
    class Meta:
        model = SupplierBid
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        exclude = ['status', 'bid']
