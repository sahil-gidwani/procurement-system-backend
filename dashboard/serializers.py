from rest_framework import serializers


class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField(required=False)
    users_by_role = serializers.JSONField(required=False)
    user_registration_over_time = serializers.JSONField(required=False)
    vendors_by_vendor_type = serializers.JSONField(required=False)
    vendor_rating_distribution = serializers.JSONField(required=False)


class ProcurementOfficerDashboardSerializer(serializers.Serializer):
    total_inventory_items = serializers.IntegerField(required=False)
    top_items_stock_quantity = serializers.JSONField(required=False)
    top_items_unit_price = serializers.JSONField(required=False)
    top_items_total_price = serializers.JSONField(required=False)
    inventory_items_added = serializers.JSONField(required=False)
    inventory_age = serializers.JSONField(required=False)
    stock_quantity_distribution = serializers.JSONField(required=False)
    total_purchase_requisitions = serializers.IntegerField(required=False)
    purchase_requisitions_by_status = serializers.JSONField(required=False)
    purchase_requisitions_over_time = serializers.JSONField(required=False)
    purchase_requisitions_age = serializers.JSONField(required=False)
    quantity_requested_distribution = serializers.JSONField(required=False)


class VendorDashboardSerializer(serializers.Serializer):
    total_supplier_bids = serializers.IntegerField(required=False)
    top_bids_bid_amount = serializers.JSONField(required=False)
    supplier_bids_by_status = serializers.JSONField(required=False)
    supplier_bids_over_time = serializers.JSONField(required=False)
    total_purchase_orders = serializers.IntegerField(required=False)
    top_orders_order_amount = serializers.JSONField(required=False)
    purchase_orders_by_status = serializers.JSONField(required=False)
    purchase_orders_over_time = serializers.JSONField(required=False)
