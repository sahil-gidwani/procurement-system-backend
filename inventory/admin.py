from django.contrib import admin
from .models import Inventory, HistoricalInventory

# Register your models here.

admin.site.register(Inventory)
admin.site.register(HistoricalInventory)
