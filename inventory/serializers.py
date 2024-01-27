from rest_framework import serializers
from .models import Inventory, HistoricalInventory, OptimizedInventory


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        exclude = ['procurement_officer']


class HistoricalInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalInventory
        exclude = ['inventory']


class OptimizedInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizedInventory
        exclude = ['inventory']
        read_only_fields = ['eoq', 'safety_stock', 'reorder_point']
