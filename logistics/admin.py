from django.contrib import admin
from .models import InventoryReceipt, Invoice

# Register your models here.

admin.site.register(InventoryReceipt)
admin.site.register(Invoice)
