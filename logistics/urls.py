from django.urls import path
from . import views

urlpatterns = [
    path(
        "inventory-receipt/list/",
        views.InventoryReceiptListView.as_view(),
        name="inventory_receipt_list",
    ),
    path(
        "inventory-receipt/create/<int:order_id>/",
        views.InventoryReceiptCreateView.as_view(),
        name="inventory_receipt_create",
    ),
    path(
        "inventory-receipt/<int:pk>/",
        views.InventoryReceiptRetrieveView.as_view(),
        name="inventory_receipt_detail",
    ),
    path(
        "inventory-receipt/<int:pk>/update/",
        views.InventoryReceiptUpdateView.as_view(),
        name="inventory_receipt_update",
    ),
    path(
        "inventory-receipt/<int:pk>/delete/",
        views.InventoryReceiptDeleteView.as_view(),
        name="inventory_receipt_delete",
    ),
]
