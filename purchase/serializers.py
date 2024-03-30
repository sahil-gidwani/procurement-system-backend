from datetime import timedelta
from rest_framework import serializers
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequisition
        read_only_fields = ["status"]
        exclude = ["inventory"]


class PurchaseRequisitionVendorSerializer(serializers.ModelSerializer):
    procurement_officer = serializers.StringRelatedField(
        source="inventory.procurement_officer"
    )
    item_name = serializers.StringRelatedField(source="inventory.item_name")

    class Meta:
        model = PurchaseRequisition
        exclude = ["status", "inventory"]


class SupplierBidSerializer(serializers.ModelSerializer):
    requisition_number = serializers.ReadOnlyField(
        source="requisition.requisition_number")

    class Meta:
        model = SupplierBid
        read_only_fields = ["status", "requisition_number"]
        exclude = ["supplier", "requisition"]


class SupplierBidProcurementOfficerSerializer(serializers.ModelSerializer):
    supplier_company_name = serializers.ReadOnlyField(
        source="supplier.vendor.user.company_name")
    supplier_rating = serializers.ReadOnlyField(source="supplier.vendor.vendor_rating")
    total_ratings = serializers.ReadOnlyField(source="supplier.vendor.total_ratings")
    weight_unit_price = serializers.FloatField(
        write_only=True, required=True, min_value=0.0, max_value=1.0)
    weight_total_cost = serializers.FloatField(
        write_only=True, required=True, min_value=0.0, max_value=1.0)
    weight_days_delivery = serializers.FloatField(
        write_only=True, required=True, min_value=0.0, max_value=1.0)
    weight_supplier_rating = serializers.FloatField(
        write_only=True, required=True, min_value=0.0, max_value=1.0)
    weight_total_ratings = serializers.FloatField(
        write_only=True, required=True, min_value=0.0, max_value=1.0)

    class Meta:
        model = SupplierBid
        read_only_fields = ["quantity_fulfilled", "unit_price", "date_submitted", "days_delivery", "attachments", "comments", "status", "supplier_company_name", "supplier_rating", "total_ratings"]
        exclude = ["requisition", "supplier"]

    def validate(self, attrs):
        weights = [
            attrs.get("weight_unit_price", 0.0),
            attrs.get("weight_total_cost", 0.0),
            attrs.get("weight_days_delivery", 0.0),
            attrs.get("weight_supplier_rating", 0.0),
            attrs.get("weight_total_ratings", 0.0),
        ]

        total_weight = sum(weights)

        if total_weight != 1.0:
            raise serializers.ValidationError(
                {
                    "weight_unit_price": "The sum of weights must be equal to 1.0",
                    "weight_total_cost": "The sum of weights must be equal to 1.0",
                    "weight_days_delivery": "The sum of weights must be equal to 1.0",
                    "weight_supplier_rating": "The sum of weights must be equal to 1.0",
                    "weight_total_ratings": "The sum of weights must be equal to 1.0",
                }
            )

        return attrs


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
