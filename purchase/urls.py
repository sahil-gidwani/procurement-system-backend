from django.urls import path
from . import views

urlpatterns = [
    path("", views.getRoutes, name="purchase_routes"),
    path(
        "purchase-requisitions/list/",
        views.PurchaseRequisitionListView.as_view(),
        name="purchase_requisition_list",
    ),
    path(
        "purchase-requisitions/create/<int:inventory_id>/",
        views.PurchaseRequisitionCreateView.as_view(),
        name="purchase_requisition_create",
    ),
    path(
        "purchase-requisitions/<int:pk>/",
        views.PurchaseRequisitionRetrieveView.as_view(),
        name="purchase_requisition_detail",
    ),
    path(
        "purchase-requisitions/<int:pk>/update/",
        views.PurchaseRequisitionUpdateView.as_view(),
        name="purchase_requisition_update",
    ),
    path(
        "purchase-requisitions/<int:pk>/delete/",
        views.PurchaseRequisitionDeleteView.as_view(),
        name="purchase_requisition_delete",
    ),
    # TODO: Change status of requisition to reject and that rejects all the bids associated with that requisition
    # path(
    #     "purchase-requisitions/<int:pk>/status/",
    #     views.PurchaseRequisitionStatusView.as_view(),
    #     name="purchase_requisition_status",
    # ),
    path(
        "purchase-requisitions/vendor/list/",
        views.PurchaseRequisitionVendorListView.as_view(),
        name="purchase_requisition_vendor_list",
    ),
    path(
        "supplier-bids/list/",
        views.SupplierBidListView.as_view(),
        name="supplier_bid_list",
    ),
    path(
        "supplier-bids/create/<int:requisition_id>/",
        views.SupplierBidCreateView.as_view(),
        name="supplier_bid_create",
    ),
    path(
        "supplier-bids/<int:pk>/",
        views.SupplierBidRetrieveView.as_view(),
        name="supplier_bid_detail",
    ),
    path(
        "supplier-bids/<int:pk>/update/",
        views.SupplierBidUpdateView.as_view(),
        name="supplier_bid_update",
    ),
    path(
        "supplier-bids/<int:pk>/delete/",
        views.SupplierBidDeleteView.as_view(),
        name="supplier_bid_delete",
    ),
    path(
        "supplier-bids/procurement-officer/list/<int:requisition_id>/",
        views.SupplierBidProcurementOfficerListView.as_view(),
        name="supplier_bid_procurement_officer_list",
    ),
    path(
        "supplier-bids/procurement-officer/list/<int:requisition_id>/ranking/",
        views.SupplierBidProcurementOfficerRankingView.as_view(),
        name="supplier_bid_procurement_officer_ranking",
    ),
    path(
        "supplier-bids/procurement-officer/<int:pk>/",
        views.SupplierBidProcurementOfficerRetrieveView.as_view(),
        name="supplier_bid_procurement_officer_detail",
    ),
    path(
        "supplier-bids/procurement-officer/<int:pk>/status/",
        views.SupplierBidProcurementOfficerStatusView.as_view(),
        name="supplier_bid_procurement_officer_status",
    ),
    path(
        "purchase-orders/list/",
        views.PurchaseOrderListView.as_view(),
        name="purchase_order_list",
    ),
    path(
        "purchase-orders/vendor/list/",
        views.PurchaseOrderVendorListView.as_view(),
        name="purchase_order_vendor_list",
    ),
    path(
        "purchase-orders/vendor/<int:pk>/status/",
        views.PurchaseOrderVendorStatusView.as_view(),
        name="purchase_order_vendor_status",
    ),
]
