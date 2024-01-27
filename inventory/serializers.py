from rest_framework import serializers
from .models import Inventory, HistoricalInventory


class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        exclude = ['procurement_officer']


class HistoricalInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalInventory
        exclude = ['inventory']
