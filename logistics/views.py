from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from drf_spectacular.utils import extend_schema
from .models import InventoryReceipt, Invoice
from .serializers import (
    InventoryReceiptSerializer,
    InvoiceSerializer,
)
from .tasks import generate_report_and_save
from purchase.models import PurchaseOrder
from accounts.permissions import IsProcurementOfficer, IsVendor


class BaseInventoryReceiptAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventoryReceiptSerializer

    def get_queryset(self):
        return InventoryReceipt.objects.filter(
            order__bid__requisition__inventory__procurement_officer=self.request.user
        )

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new inventory receipt
        # Return the object of InventoryInspection based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder, id=order_id,
        )
        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order.")
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class InventoryReceiptListView(BaseInventoryReceiptAPIView, generics.ListAPIView):
    pass


class InventoryReceiptCreateView(
    BaseInventoryReceiptAPIView, generics.CreateAPIView
):
    queryset = InventoryReceipt.objects.all()

    def perform_create(self, serializer):
        order_id = self.kwargs.get("order_id")
        order = get_object_or_404(
            PurchaseOrder, id=order_id,
        )

        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )

        existing_receipt = InventoryReceipt.objects.filter(order=order).exists()
        if existing_receipt:
            raise ValidationError("Inventory receipt already exists for this order.")
        
        instance = serializer.save(order=order)

        generate_report_and_save.delay(instance.id, 'inventory_receipt')


class InventoryReceiptRetrieveView(
    BaseInventoryReceiptAPIView, generics.RetrieveAPIView
):
    pass


class InventoryReceiptUpdateView(
    BaseInventoryReceiptAPIView, generics.UpdateAPIView
):
    queryset = InventoryReceipt.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status == 'inspected':
            raise serializers.ValidationError(
                {"status": "Inventory is already inspected."}
            )

        serializer.save()

        # send_requisition_update_email.delay(instance.id)
        generate_report_and_save.delay(instance.id, 'inventory_receipt')
    
    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response({"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST)
        return super().patch(request, *args, **kwargs)


class InventoryReceiptDeleteView(
    BaseInventoryReceiptAPIView, generics.DestroyAPIView
):
    queryset = InventoryReceipt.objects.all()

    def perform_destroy(self, instance):
        if instance.status == 'inspected':
            raise serializers.ValidationError(
                {"status": "Inventory is already inspected."}
            )
        instance.delete()
