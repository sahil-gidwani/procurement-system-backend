from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import PurchaseRequisition
from .serializers import PurchaseRequisitionSerializer
from inventory.models import Inventory
from accounts.permissions import IsProcurementOfficer


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
