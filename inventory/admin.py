from django.contrib import admin
from .models import Inventory, HistoricalInventory, OptimizedInventory

# Register your models here.

admin.site.register(Inventory)
admin.site.register(HistoricalInventory)
admin.site.register(OptimizedInventory)
