from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder
from .serializers import PurchaseRequisitionSerializer, PurchaseRequisitionVendorSerializer, SupplierBidSerializer, SupplierBidProcurementOfficerSerializer, PurchaseOrderSerializer
from inventory.models import Inventory
from accounts.permissions import IsProcurementOfficer, IsVendor


class BasePurchaseRequisitionAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = PurchaseRequisitionSerializer

    def get_queryset(self):
        return PurchaseRequisition.objects.filter(inventory__procurement_officer=self.request.user)

    def get_object(self):
        inventory_id = self.kwargs.get("inventory_id")

        # If inventory_id is None, then we are not creating a new purchase requisition
        if inventory_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))
        
        inventory = get_object_or_404(Inventory, id=inventory_id, procurement_officer=self.request.user)
        obj = get_object_or_404(self.get_queryset(), inventory=inventory)
        self.check_object_permissions(self.request, obj)
        return obj


class PurchaseRequisitionListView(BasePurchaseRequisitionAPIView, generics.ListAPIView):
    pass


class PurchaseRequisitionCreateView(BasePurchaseRequisitionAPIView, generics.CreateAPIView):
    queryset = PurchaseRequisition.objects.all()

    def perform_create(self, serializer):
        inventory_id = self.kwargs.get("inventory_id")
        inventory = get_object_or_404(Inventory, pk=inventory_id, procurement_officer=self.request.user)
        serializer.save(inventory=inventory)


class PurchaseRequisitionRetrieveView(BasePurchaseRequisitionAPIView, generics.RetrieveAPIView):
    pass


class PurchaseRequisitionUpdateView(BasePurchaseRequisitionAPIView, generics.UpdateAPIView):
    pass


class PurchaseRequisitionDeleteView(BasePurchaseRequisitionAPIView, generics.DestroyAPIView):
    pass


class PurchaseRequisitionVendorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = PurchaseRequisitionVendorSerializer
    queryset = PurchaseRequisition.objects.all()


class BaseSupplierAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = SupplierBidSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(supplier=self.request.user)

    def get_object(self):
        requisition_id = self.kwargs.get("requisition_id")

        # If requisition_id is None, then we are not creating a new supplier bid
        if requisition_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))
        
        requisition = get_object_or_404(PurchaseRequisition, id=requisition_id)
        obj = get_object_or_404(self.get_queryset(), requisition=requisition)
        self.check_object_permissions(self.request, obj)
        return obj


class SupplierBidListView(BaseSupplierAPIView, generics.ListAPIView):
    pass


class SupplierBidCreateView(BaseSupplierAPIView, generics.CreateAPIView):
    queryset = SupplierBid.objects.all()

    def perform_create(self, serializer):
        requisition_id = self.kwargs.get("requisition_id")
        requisition = get_object_or_404(PurchaseRequisition, pk=requisition_id)
        serializer.save(requisition=requisition, supplier=self.request.user)


class SupplierBidRetrieveView(BaseSupplierAPIView, generics.RetrieveAPIView):
    pass


class SupplierBidUpdateView(BaseSupplierAPIView, generics.UpdateAPIView):
    pass


class SupplierBidDeleteView(BaseSupplierAPIView, generics.DestroyAPIView):
    pass


class SupplierBidProcurementOfficerListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(requisition__inventory__procurement_officer=self.request.user, requisition__id=self.kwargs.get("requisition_id"))


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        "/purchase-requisitions/list",
        "/purchase-requisitions/create/<int:inventory_id>",
        "/purchase-requisitions/<int:pk>",
        "/purchase-requisitions/<int:pk>/update",
        "/purchase-requisitions/<int:pk>/delete",
        "/purcase-requisitions/vendor/list",
        "/supplier-bids/list",
        "/supplier-bids/create/<int:requisition_id>",
        "/supplier-bids/<int:pk>",
        "/supplier-bids/<int:pk>/update",
        "/supplier-bids/<int:pk>/delete",
        "/supplier-bids/procurement-officer/list/<int:requisition_id>",
    ]

    return Response(routes)
