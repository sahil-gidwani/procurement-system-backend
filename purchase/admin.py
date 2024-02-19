from django.contrib import admin
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder

# Register your models here.

admin.site.register(PurchaseRequisition)
admin.site.register(SupplierBid)
admin.site.register(PurchaseOrder)
