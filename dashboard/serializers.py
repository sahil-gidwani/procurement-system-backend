from rest_framework import serializers


class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    users_by_role = serializers.JSONField()
    user_registration_over_time = serializers.JSONField()
    vendors_by_vendor_type = serializers.JSONField()
    vendor_rating_distribution = serializers.JSONField()


class ProcurementOfficerDashboardSerializer(serializers.Serializer):
    total_inventory_items = serializers.IntegerField()
    top_items_stock_quantity = serializers.JSONField()
    top_items_unit_price = serializers.JSONField()
    top_items_total_price = serializers.JSONField()
    inventory_items_added = serializers.JSONField()
    inventory_age = serializers.JSONField()
    stock_quantity_distribution = serializers.JSONField()
    total_purchase_requisitions = serializers.IntegerField()
    purchase_requisitions_by_status = serializers.JSONField()
    purchase_requisitions_over_time = serializers.JSONField()
    purchase_requisitions_age = serializers.JSONField()
    quantity_requested_distribution = serializers.JSONField()


class VendorDashboardSerializer(serializers.Serializer):
    total_supplier_bids = serializers.IntegerField()
    top_bids_bid_amount = serializers.JSONField()
    supplier_bids_by_status = serializers.JSONField()
    supplier_bids_over_time = serializers.JSONField()
    total_purchase_orders = serializers.IntegerField()
    top_orders_order_amount = serializers.JSONField()
    purchase_orders_by_status = serializers.JSONField()
    purchase_orders_over_time = serializers.JSONField()
