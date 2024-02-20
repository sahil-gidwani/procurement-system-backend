from django.urls import path
from . import views

urlpatterns = [
    path("", views.getRoutes, name="purchase_routes"),
    path('purchase-requisitions/list/', views.PurchaseRequisitionListView.as_view(), name='purchase_requisition_list'),
    path('purchase-requisitions/create/<int:inventory_id>/', views.PurchaseRequisitionCreateView.as_view(), name='purchase_requisition_create'),
    path('purchase-requisitions/<int:pk>/', views.PurchaseRequisitionRetrieveView.as_view(), name='purchase_requisition_detail'),
    path('purchase-requisitions/<int:pk>/update/', views.PurchaseRequisitionUpdateView.as_view(), name='purchase_requisition_update'),
    path('purchase-requisitions/<int:pk>/delete/', views.PurchaseRequisitionDeleteView.as_view(), name='purchase_requisition_delete'),
    path('purcase-requisitions/vendor/list/', views.PurchaseRequisitionVendorListView.as_view(), name='purchase_requisition_vendor_list'),
    path('supplier-bids/list/', views.SupplierBidListView.as_view(), name='supplier_bid_list'),
    path('supplier-bids/create/<int:requisition_id>/', views.SupplierBidCreateView.as_view(), name='supplier_bid_create'),
    path('supplier-bids/<int:pk>/', views.SupplierBidRetrieveView.as_view(), name='supplier_bid_detail'),
    path('supplier-bids/<int:pk>/update/', views.SupplierBidUpdateView.as_view(), name='supplier_bid_update'),
    path('supplier-bids/<int:pk>/delete/', views.SupplierBidDeleteView.as_view(), name='supplier_bid_delete'),
    path('supplier-bids/procurement-officer/list/<int:requisition_id>/', views.SupplierBidProcurementOfficerListView.as_view(), name='supplier_bid_procurement_officer_list'),
]
