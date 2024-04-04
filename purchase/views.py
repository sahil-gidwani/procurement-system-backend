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
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder
from .serializers import (
    PurchaseRequisitionSerializer,
    PurchaseRequisitionVendorSerializer,
    SupplierBidSerializer,
    SupplierBidProcurementOfficerSerializer,
    SupplierBidProcurementOfficerStatusSerializer,
    PurchaseOrderSerializer,
    PurchaseOrderStatusSerializer,
)
from .tasks import (
    send_requisition_update_email,
    send_supplier_bid_email,
    send_supplier_bid_update_email,
    send_bid_accepted_email,
    send_bid_rejected_email,
    send_requisition_accepted_email,
    send_purchase_order_email,
    send_purchase_order_status_email,
)
from inventory.models import Inventory
from accounts.permissions import IsProcurementOfficer, IsVendor


class BasePurchaseRequisitionAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = PurchaseRequisitionSerializer

    def get_queryset(self):
        return PurchaseRequisition.objects.filter(
            inventory__procurement_officer=self.request.user
        )

    def get_object(self):
        inventory_id = self.kwargs.get("inventory_id")

        # If inventory_id is None, then we are not creating a new purchase requisition
        # Return the object of PurchaseRequisition based on the primary key
        if inventory_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        inventory = get_object_or_404(
            Inventory,
            id=inventory_id,
        )
        if inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this inventory item."
            )
        obj = get_object_or_404(self.get_queryset(), inventory=inventory)

        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class PurchaseRequisitionListView(BasePurchaseRequisitionAPIView, generics.ListAPIView):
    pass


class PurchaseRequisitionCreateView(
    BasePurchaseRequisitionAPIView, generics.CreateAPIView
):
    queryset = PurchaseRequisition.objects.all()

    def perform_create(self, serializer):
        inventory_id = self.kwargs.get("inventory_id")
        inventory = get_object_or_404(Inventory, pk=inventory_id)

        if inventory.procurement_officer != self.request.user:
            raise PermissionDenied(
                "You do not have permission to access this inventory item."
            )

        existing_requisition = PurchaseRequisition.objects.filter(
            inventory=inventory
        ).exists()
        if existing_requisition:
            raise ValidationError("A requisition for this inventory already exists.")

        serializer.save(inventory=inventory)


class PurchaseRequisitionRetrieveView(
    BasePurchaseRequisitionAPIView, generics.RetrieveAPIView
):
    pass


class PurchaseRequisitionUpdateView(
    BasePurchaseRequisitionAPIView, generics.UpdateAPIView
):
    queryset = PurchaseRequisition.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.status == "approved":
            raise serializers.ValidationError(
                {"status": "Requisition is already approved."}
            )

        serializer.validated_data["status"] = "pending"
        serializer.save()

        send_requisition_update_email.delay(instance.id)

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


class PurchaseRequisitionDeleteView(
    BasePurchaseRequisitionAPIView, generics.DestroyAPIView
):
    queryset = PurchaseRequisition.objects.all()

    def perform_destroy(self, instance):
        if instance.status == "approved":
            raise serializers.ValidationError(
                {"status": "Requisition is already approved."}
            )
        instance.delete()


# @method_decorator(cache_page(60 * 15), name="dispatch")
class PurchaseRequisitionVendorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = PurchaseRequisitionVendorSerializer
    queryset = PurchaseRequisition.objects.filter(status="pending")


class BaseSupplierAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = SupplierBidSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(supplier=self.request.user)

    def get_object(self):
        requisition_id = self.kwargs.get("requisition_id")

        # If requisition_id is None, then we are not creating a new supplier bid
        # Return the object of SupplierBid based on the primary key
        if requisition_id is None:
            return get_object_or_404(self.get_queryset(), id=self.kwargs.get("pk"))

        requisition = get_object_or_404(PurchaseRequisition, id=requisition_id)
        obj = get_object_or_404(self.get_queryset(), requisition=requisition)
        return obj


# @method_decorator(cache_page(60 * 15), name="dispatch")
class SupplierBidListView(BaseSupplierAPIView, generics.ListAPIView):
    pass


class SupplierBidCreateView(BaseSupplierAPIView, generics.CreateAPIView):
    queryset = SupplierBid.objects.all()

    def perform_create(self, serializer):
        requisition_id = self.kwargs.get("requisition_id")
        requisition = get_object_or_404(PurchaseRequisition, pk=requisition_id)

        if requisition.status == "approved" or requisition.status == "rejected":
            raise serializers.ValidationError(
                {"status": "Requisition is already approved or rejected."}
            )

        # Validate quantity_fulfilled against requisition.quantity_requested
        quantity_fulfilled = serializer.validated_data.get("quantity_fulfilled")
        if (
            quantity_fulfilled is not None
            and quantity_fulfilled < requisition.quantity_requested
        ):
            raise serializers.ValidationError(
                {
                    "quantity_fulfilled": f"Quantity fulfilled must be greater than or equal to quantity requested ({requisition.quantity_requested})."
                }
            )

        try:
            serializer.save(requisition=requisition, supplier=self.request.user)
            send_supplier_bid_email.delay(
                requisition.inventory.procurement_officer.email,
                self.request.user.company_name,
                requisition.requisition_number,
            )
        except IntegrityError:
            raise ValidationError(
                "A SupplierBid for this requisition and supplier already exists."
            )


class SupplierBidRetrieveView(BaseSupplierAPIView, generics.RetrieveAPIView):
    pass


class SupplierBidUpdateView(BaseSupplierAPIView, generics.UpdateAPIView):
    queryset = SupplierBid.objects.all()

    def perform_update(self, serializer):
        instance = self.get_object()
        requisition = instance.requisition

        # Prevent updating the bid if it is already accepted
        if instance.status == "accepted":
            raise serializers.ValidationError({"status": "Bid is already accepted."})

        # Validate quantity_fulfilled against requisition.quantity_requested
        quantity_fulfilled = serializer.validated_data.get("quantity_fulfilled")
        if (
            quantity_fulfilled is not None
            and quantity_fulfilled < requisition.quantity_requested
        ):
            raise serializers.ValidationError(
                {
                    "quantity_fulfilled": f"Quantity fulfilled must be greater than or equal to quantity requested ({requisition.quantity_requested})."
                }
            )

        # Reset status to submitted if the bid is not accepted
        serializer.validated_data["status"] = "submitted"

        serializer.save(requisition=requisition, supplier=self.request.user)

        send_supplier_bid_update_email.delay(
            requisition.inventory.procurement_officer.email,
            self.request.user.company_name,
            requisition.requisition_number,
        )

    def patch(self, request, *args, **kwargs):
        if not request.data:
            return Response(
                {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
            )
        return super().patch(request, *args, **kwargs)


class SupplierBidDeleteView(BaseSupplierAPIView, generics.DestroyAPIView):
    queryset = SupplierBid.objects.all()

    def perform_destroy(self, instance):
        if instance.status == "accepted":
            raise serializers.ValidationError({"status": "Bid is already accepted."})
        instance.delete()


# @method_decorator(cache_page(60 * 15), name="dispatch")
class SupplierBidProcurementOfficerListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(
            requisition__inventory__procurement_officer=self.request.user,
            requisition__id=self.kwargs.get("requisition_id"),
        )


# @method_decorator(cache_page(60 * 15), name="dispatch")
class SupplierBidProcurementOfficerRankingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerSerializer

    def post(self, request, requisition_id, *args, **kwargs):
        requisition = get_object_or_404(
            PurchaseRequisition,
            id=requisition_id,
            inventory__procurement_officer=self.request.user,
        )
        bids = SupplierBid.objects.filter(requisition=requisition)

        # Check if there are at least two bids
        if bids.count() < 2:
            return Response(
                {"error": "There must be at least two bids to perform ranking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(bids, many=True)
        data = serializer.data

        df = pd.DataFrame(data)
        df["unit_price"] = pd.to_numeric(df["unit_price"])
        df["quantity_fulfilled"] = pd.to_numeric(df["quantity_fulfilled"])
        df["days_delivery"] = pd.to_numeric(df["days_delivery"])
        df["supplier_rating"] = pd.to_numeric(df["supplier_rating"])
        df["total_ratings"] = pd.to_numeric(df["total_ratings"])
        df["total_cost"] = df["unit_price"] * df["quantity_fulfilled"]

        # Multi-Criteria Evaluation using TOPSIS - Technique for Order of Preference by Similarity to Ideal Solution

        # 1. Normalize the Decision Matrix
        norm_df = df.copy()
        norm_df = norm_df[
            [
                "unit_price",
                "total_cost",
                "days_delivery",
                "supplier_rating",
                "total_ratings",
            ]
        ]
        norm_df = (norm_df - norm_df.min()) / (norm_df.max() - norm_df.min())

        # 2. Define weights for each criterion
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        weights = {
            "unit_price": serializer.validated_data["weight_unit_price"],
            "total_cost": serializer.validated_data["weight_total_cost"],
            "days_delivery": serializer.validated_data["weight_days_delivery"],
            "supplier_rating": serializer.validated_data["weight_supplier_rating"],
            "total_ratings": serializer.validated_data["weight_total_ratings"],
        }

        # 3. Multiply the normalized decision matrix by the weights to get the weighted normalized decision matrix
        for col in norm_df.columns:
            norm_df[col] *= weights[col]

        # 4. Determine the positive ideal solution (PIS) and negative ideal solution (NIS)
        PIS = pd.Series(
            {
                "unit_price": norm_df["unit_price"].min(),
                "total_cost": norm_df["total_cost"].min(),
                "days_delivery": norm_df["days_delivery"].min(),
                "supplier_rating": norm_df["supplier_rating"].max(),
                "total_ratings": norm_df["total_ratings"].max(),
            }
        )

        NIS = pd.Series(
            {
                "unit_price": norm_df["unit_price"].max(),
                "total_cost": norm_df["total_cost"].max(),
                "days_delivery": norm_df["days_delivery"].max(),
                "supplier_rating": norm_df["supplier_rating"].min(),
                "total_ratings": norm_df["total_ratings"].min(),
            }
        )

        # 5. Calculate euclidean distances from PIS and NIS
        dist_PIS = np.sqrt(((norm_df - PIS) ** 2).sum(axis=1))
        dist_NIS = np.sqrt(((norm_df - NIS) ** 2).sum(axis=1))

        # 6. Calculate relative closeness
        closeness = dist_NIS / (dist_PIS + dist_NIS)
        df["closeness"] = closeness
        norm_df["closeness"] = closeness

        # 7. Rank the alternatives based on closeness values
        df["rank"] = df["closeness"].rank(ascending=False)
        norm_df["rank"] = norm_df["closeness"].rank(ascending=False)

        # Sort the dataframes by rank
        df = df.sort_values(by="rank")
        norm_df = norm_df.sort_values(by="rank")

        df_json = df.to_json(orient="records")

        # Create the radar chart
        criteria = [
            "unit_price",
            "total_cost",
            "days_delivery",
            "supplier_rating",
            "total_ratings",
        ]
        norm_values = norm_df.values.tolist()
        alternative_names = list(norm_df["rank"])
        fig = go.Figure()
        for name, values in zip(alternative_names, norm_values):
            fig.add_trace(
                go.Scatterpolar(r=values, theta=criteria, fill="toself", name=name)
            )
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                )
            ),
            showlegend=True,
            title="Multi-Criteria Evaluation of Bids: Radar Chart Ranking",
        )
        radar_plot_json = pio.to_json(fig)

        # Create a parallel coordinates plot
        fig = px.parallel_coordinates(
            df,
            color="rank",
            color_continuous_scale=px.colors.sequential.Viridis,
            labels={"rank": "Rank"},
            dimensions=[
                "unit_price",
                "total_cost",
                "days_delivery",
                "supplier_rating",
                "total_ratings",
            ],
        )
        fig.update_layout(
            title="Multi-Criteria Evaluation: Parallel Coordinates of Bids Ranking",
            title_x=0.5,
            title_y=0.05,
        )
        parallel_plot_json = pio.to_json(fig)

        response_data = {
            "dataframe": df_json,
            "radar_plot": radar_plot_json,
            "parallel_plot": parallel_plot_json,
        }
        return Response(response_data, content_type="application/json")


class SupplierBidProcurementOfficerRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(
            requisition__inventory__procurement_officer=self.request.user,
            id=self.kwargs.get("pk"),
        )


class SupplierBidProcurementOfficerStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerStatusSerializer

    def get_queryset(self):
        return SupplierBid.objects.filter(
            requisition__inventory__procurement_officer=self.request.user,
            id=self.kwargs.get("pk"),
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if "status" not in serializer.validated_data:
            return Response(
                {"error": "Bid status is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        bid_status = serializer.validated_data.get("status")

        if bid_status not in ["accepted", "rejected"]:
            return Response(
                {"error": "Bid status can only be 'accepted' or 'rejected'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if instance.status != "submitted":
            return Response(
                {"error": "Bid status already modified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Custom logic for updating requisition and creating purchase order
        if bid_status == "accepted":
            requisition = instance.requisition
            if SupplierBid.objects.filter(
                requisition=requisition, status="accepted"
            ).exists():
                # If another bid is already accepted, do not update the status
                return Response(
                    {"error": "Another bid is already accepted for this requisition."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # No other bids are accepted, proceed with the update
            self.perform_update(serializer)
            send_bid_accepted_email.delay(
                instance.supplier.email, instance.id, requisition.requisition_number
            )

            requisition.status = "approved"
            requisition.save()
            send_requisition_accepted_email.delay(
                requisition.inventory.procurement_officer.email,
                requisition.requisition_number,
            )

            # Reject all other bids associated with the requisition
            other_bids = SupplierBid.objects.filter(requisition=requisition).exclude(
                id=instance.id
            )
            other_bids.update(status="rejected")

            # Convert the QuerySet to a list and extract the email addresses
            supplier_emails = list(other_bids.values_list("supplier__email", flat=True))
            send_bid_rejected_email.delay(
                supplier_emails, instance.id, requisition.requisition_number
            )

            # Create a purchase order automatically
            purchase_order = PurchaseOrder.objects.create(
                order_number=f"PO-{requisition.requisition_number}",
                bid_id=instance.id,
            )
            purchase_order.save()
            send_purchase_order_email.delay(
                [
                    instance.supplier.email,
                    requisition.inventory.procurement_officer.email,
                ],
                instance.id,
                requisition.requisition_number,
                purchase_order.order_number,
            )

            return Response(serializer.data)

        elif bid_status == "rejected":
            # Only perform serializer update if bid is rejected
            self.perform_update(serializer)
            send_bid_rejected_email.delay(
                [instance.supplier.email],
                instance.id,
                instance.requisition.requisition_number,
            )
            return Response(serializer.data)


# @method_decorator(cache_page(60 * 15), name="dispatch")
class PurchaseOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.filter(
            bid__requisition__inventory__procurement_officer=self.request.user
        )


# @method_decorator(cache_page(60 * 15), name="dispatch")
class PurchaseOrderVendorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = PurchaseOrderSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.filter(bid__supplier=self.request.user)


class PurchaseOrderVendorStatusView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = PurchaseOrderStatusSerializer

    def get_queryset(self):
        return PurchaseOrder.objects.filter(
            bid__supplier=self.request.user,
            id=self.kwargs.get("pk"),
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")

        # Check if the status transition is valid
        if instance.status == "delivered":
            return Response(
                {"error": "Order is already delivered."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif instance.status == "shipped" and new_status == "shipped":
            return Response(
                {"error": "Order is already shipped."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif new_status not in ["shipped", "delivered"]:
            return Response(
                {"error": "Invalid status transition."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif new_status == "delivered" and instance.status != "shipped":
            return Response(
                {"error": "Order must be shipped before it can be delivered."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = new_status
        instance.save()
        send_purchase_order_status_email.delay(
            instance.bid.requisition.inventory.procurement_officer.email,
            instance.order_number,
            new_status,
        )

        return Response(serializer.data)


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
        "/supplier-bids/procurement-officer/list/<int:requisition_id>/ranking",
        "/supplier-bids/procurement-officer/<int:pk>",
        "/supplier-bids/procurement-officer/<int:pk>/status",
        "/purchase-orders/list",
        "/purchase-orders/vendor/list",
        "/purchase-orders/vendor/<int:pk>/status",
    ]

    return Response(routes)
