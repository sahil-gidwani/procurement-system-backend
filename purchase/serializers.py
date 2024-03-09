from datetime import timedelta
from rest_framework import serializers
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        exclude = ["status", "inventory"]


class PurchaseRequisitionVendorSerializer(serializers.ModelSerializer):
    procurement_officer = serializers.StringRelatedField(
        source="inventory.procurement_officer"
    )

    class Meta:
        model = PurchaseRequisition
        exclude = ["status", "inventory"]


class SupplierBidSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBid
        exclude = ["status", "requisition", "supplier"]
    
    def validate_quantity_fulfilled(self, value):
        requisition = self.initial_data.get("requisition")

        if requisition and value < requisition.quantity_requested:
            raise serializers.ValidationError(
                f"Quantity fulfilled must be greater than or equal to quantity requested ({requisition.quantity_requested})."
            )
        return value


class SupplierBidProcurementOfficerSerializer(serializers.ModelSerializer):
    supplier_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()

    class Meta:
        model = SupplierBid
        exclude = ["requisition"]

    def get_supplier_rating(self, instance) -> float:
        return instance.supplier.vendor.vendor_rating

    def get_total_ratings(self, instance) -> int:
        return instance.supplier.vendor.total_ratings


class SupplierBidProcurementOfficerStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBid
        fields = ["status"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    quantity_ordered = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    expected_delivery_date = serializers.SerializerMethodField()
    class Meta:
        model = PurchaseOrder
        fields = "__all__"
    
    def get_quantity_ordered(self, instance) -> int:
        return instance.bid.quantity_fulfilled
    
    def get_unit_price(self, instance) -> float:
        return instance.bid.unit_price
    
    def get_expected_delivery_date(self, instance) -> str:
        return instance.date_ordered + timedelta(days=instance.bid.days_delivery)


class PurchaseOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = ["status"]
