from rest_framework import serializers
from .models import Inventory, HistoricalInventory

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = '__all__'

class HistoricalInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalInventory
        fields = '__all__'
