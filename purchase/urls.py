from django.urls import path
from . import views

urlpatterns = [
    path('purchase-requisitions/list/', views.PurchaseRequisitionListView.as_view(), name='purchase_requisition_list'),
    path('purchase-requisitions/create/<int:inventory_id>/', views.PurchaseRequisitionCreateView.as_view(), name='purchase_requisition_create'),
    path('purchase-requisitions/<int:pk>/', views.PurchaseRequisitionRetrieveView.as_view(), name='purchase_requisition_detail'),
    path('purchase-requisitions/<int:pk>/update/', views.PurchaseRequisitionUpdateView.as_view(), name='purchase_requisition_update'),
    path('purchase-requisitions/<int:pk>/delete/', views.PurchaseRequisitionDeleteView.as_view(), name='purchase_requisition_delete'),
]
