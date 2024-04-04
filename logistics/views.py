from django.shortcuts import get_object_or_404
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
    InvoicePaymentStatusSerializer,
    InvoiceVendorRatingSerializer,
)
from .tasks import generate_report_and_save, send_logistics_email
from purchase.models import PurchaseOrder
from accounts.models import Vendor
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
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class InventoryReceiptListView(BaseInventoryReceiptAPIView, generics.ListAPIView):
    pass


class InventoryReceiptCreateView(BaseInventoryReceiptAPIView, generics.CreateAPIView):
    queryset = InventoryReceipt.objects.all()

    def perform_create(self, serializer):
        order_id = self.kwargs.get("order_id")
        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )

        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )

        if order.status != "delivered":
            raise ValidationError("Order is not delivered yet.")

        existing_receipt = InventoryReceipt.objects.filter(order=order).exists()
        if existing_receipt:
            raise ValidationError("Inventory receipt already exists for this order.")

        instance = serializer.save(order=order)

        generate_report_and_save.delay(instance.id, "inventory_receipt")
        send_logistics_email.delay(
            instance.id, type="inventory_receipt", action="created"
        )


class InventoryReceiptRetrieveView(
    BaseInventoryReceiptAPIView, generics.RetrieveAPIView
):
    pass


class InventoryReceiptUpdateView(BaseInventoryReceiptAPIView, generics.UpdateAPIView):
    queryset = InventoryReceipt.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        # if instance.status == 'inspected':
        #     raise serializers.ValidationError(
        #         {"status": "Inventory is already inspected."}
        #     )

        serializer.save()

        generate_report_and_save.delay(instance.id, "inventory_receipt")
        send_logistics_email.delay(
            instance.id, type="inventory_receipt", action="updated"
        )

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


class InventoryReceiptDeleteView(BaseInventoryReceiptAPIView, generics.DestroyAPIView):
    queryset = InventoryReceipt.objects.all()

    def perform_destroy(self, instance):
        # if instance.status == 'inspected':
        #     raise serializers.ValidationError(
        #         {"status": "Inventory is already inspected."}
        #     )
        instance.delete()


class BaseInventoryReceiptVendorAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = InventoryReceiptSerializer

    def get_queryset(self):
        return InventoryReceipt.objects.filter(order__bid__supplier=self.request.user)

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new invoice
        # Return the object of Invoice based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.supplier != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class InventoryReceiptVendorListView(
    BaseInventoryReceiptVendorAPIView, generics.ListAPIView
):
    pass


class InventoryReceiptVendorRetrieveView(
    BaseInventoryReceiptVendorAPIView, generics.RetrieveAPIView
):
    pass


class BaseInvoiceAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(order__bid__supplier=self.request.user)

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new invoice
        # Return the object of Invoice based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.supplier != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class InvoiceListView(BaseInvoiceAPIView, generics.ListAPIView):
    pass


class InvoiceCreateView(BaseInvoiceAPIView, generics.CreateAPIView):
    queryset = Invoice.objects.all()

    def perform_create(self, serializer):
        order_id = self.kwargs.get("order_id")
        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )

        if order.bid.supplier != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )

        if order.status != "delivered":
            raise ValidationError("Order is not delivered yet.")

        existing_invoice = Invoice.objects.filter(order=order).exists()
        if existing_invoice:
            raise ValidationError("Invoice already exists for this order.")

        instance = serializer.save(order=order)

        generate_report_and_save.delay(instance.id, "invoice")
        send_logistics_email.delay(instance.id, type="invoice", action="created")


class InvoiceRetrieveView(BaseInvoiceAPIView, generics.RetrieveAPIView):
    pass


class InvoiceUpdateView(BaseInvoiceAPIView, generics.UpdateAPIView):
    queryset = Invoice.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.payment_status == "paid":
            raise serializers.ValidationError(
                {"payment_status": "Invoice is already paid."}
            )

        serializer.save()

        generate_report_and_save.delay(instance.id, "invoice")
        send_logistics_email.delay(instance.id, type="invoice", action="updated")

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


class InvoiceDeleteView(BaseInvoiceAPIView, generics.DestroyAPIView):
    queryset = Invoice.objects.all()

    def perform_destroy(self, instance):
        if instance.payment_status == "paid":
            raise serializers.ValidationError(
                {"payment_status": "Invoice is already paid."}
            )
        instance.delete()


class BaseInvoiceProcurementOfficerAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(
            order__bid__requisition__inventory__procurement_officer=self.request.user
        )

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new inventory receipt
        # Return the object of InventoryInspection based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class InvoiceProcurementOfficerListView(
    BaseInvoiceProcurementOfficerAPIView, generics.ListAPIView
):
    pass


class InvoiceProcurementOfficerRetrieveView(
    BaseInvoiceProcurementOfficerAPIView, generics.RetrieveAPIView
):
    pass


class InvoicePaymentStatusUpdateView(generics.UpdateAPIView):
    serializer_class = InvoicePaymentStatusSerializer
    permission_classes = [IsAuthenticated, IsProcurementOfficer]

    def get_queryset(self):
        return Invoice.objects.filter(
            order__bid__requisition__inventory__procurement_officer=self.request.user
        )

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new invoice
        # Return the object of Invoice based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.payment_status == "paid":
            raise serializers.ValidationError(
                {"payment_status": "Invoice is already paid."}
            )

        serializer.save()

        generate_report_and_save.delay(instance.id, "invoice")
        send_logistics_email.delay(
            instance.id, type="invoice", action="payment_received"
        )

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


class InvoiceVendorRatingUpdateView(generics.UpdateAPIView):
    serializer_class = InvoiceVendorRatingSerializer
    permission_classes = [IsAuthenticated, IsProcurementOfficer]

    def get_queryset(self):
        return Invoice.objects.filter(
            order__bid__requisition__inventory__procurement_officer=self.request.user
        )

    def get_object(self):
        order_id = self.kwargs.get("order_id")

        # If order_id is None, then we are not creating a new invoice
        # Return the object of Invoice based on the primary key
        if order_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        order = get_object_or_404(
            PurchaseOrder,
            id=order_id,
        )
        if order.bid.requisition.inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this purchase order."
            )
        obj = get_object_or_404(self.get_queryset(), order=order)

        return obj

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.vendor_rated:
            raise serializers.ValidationError(
                {"vendor_rated": "Vendor is already rated."}
            )

        if instance.payment_status != "paid":
            raise serializers.ValidationError(
                {"payment_status": "Invoice is not paid yet."}
            )

        # Get the vendor object
        vendor = Vendor.objects.get(user=instance.order.bid.supplier)

        # Calculate the average vendor rating
        total_ratings = vendor.total_ratings
        current_rating = vendor.vendor_rating
        new_rating = (
            total_ratings * current_rating + serializer.validated_data["vendor_rating"]
        ) / (total_ratings + 1)

        # Update the vendor rating and total ratings
        vendor.vendor_rating = new_rating
        vendor.total_ratings += 1
        vendor.save()

        serializer.save(vendor_rated=True)

        send_logistics_email.delay(instance.id, type="invoice", action="vendor_rated")

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        "/inventory-receipt/list/",
        "/inventory-receipt/create/<int:order_id>/",
        "/inventory-receipt/<int:pk>/",
        "/inventory-receipt/<int:pk>/update/",
        "/inventory-receipt/<int:pk>/delete/",
        "/inventory-receipt/vendor/list/",
        "/inventory-receipt/vendor/<int:pk>/",
        "/invoice/list/",
        "/invoice/create/<int:order_id>/",
        "/invoice/<int:pk>/",
        "/invoice/<int:pk>/update/",
        "/invoice/<int:pk>/delete/",
        "/invoice/procurement-officer/list/",
        "/invoice/procurement-officer/<int:pk>/",
        "/invoice/<int:pk>/payment-status/",
        "/invoice/<int:pk>/vendor-rating/",
    ]

    return Response(routes)
