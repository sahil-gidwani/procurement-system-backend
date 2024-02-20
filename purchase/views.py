from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
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


class SupplierBidProcurementOfficerRankingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = SupplierBidProcurementOfficerSerializer

    def get(self, request, requisition_id, *args, **kwargs):
        requisition = get_object_or_404(PurchaseRequisition, id=requisition_id, inventory__procurement_officer=self.request.user)
        bids = SupplierBid.objects.filter(requisition=requisition)
        serializer = self.serializer_class(bids, many=True)
        data = serializer.data

        df = pd.DataFrame(data)
        df['unit_price'] = pd.to_numeric(df['unit_price'])
        df['quantity_fulfilled'] = pd.to_numeric(df['quantity_fulfilled'])
        df['days_delivery'] = pd.to_numeric(df['days_delivery'])
        df['supplier_rating'] = pd.to_numeric(df['supplier_rating'])
        df['total_cost'] = df['unit_price'] * df['quantity_fulfilled']

        # Multi-Criteria Evaluation using TOPSIS - Technique for Order of Preference by Similarity to Ideal Solution

        # 1. Normalize the Decision Matrix
        norm_df = df.copy()
        norm_df = norm_df[['unit_price', 'total_cost', 'days_delivery', 'supplier_rating']]
        norm_df = (norm_df - norm_df.min()) / (norm_df.max() - norm_df.min())

        # 2. Define weights for each criterion
        weights = {
            'unit_price': 0.125,
            'days_delivery': 0.125,
            'supplier_rating': 0.25,
            'total_cost': 0.5
        }

        # 3. Multiply the normalized decision matrix by the weights to get the weighted normalized decision matrix
        for col in norm_df.columns:
            norm_df[col] *= weights[col]
        
        # 4. Determine the positive ideal solution (PIS) and negative ideal solution (NIS)
        PIS = pd.Series({
            'unit_price': norm_df['unit_price'].min(),
            'days_delivery': norm_df['days_delivery'].min(),
            'supplier_rating': norm_df['supplier_rating'].max(),
            'total_cost': norm_df['total_cost'].min()
        })

        NIS = pd.Series({
            'unit_price': norm_df['unit_price'].max(),
            'days_delivery': norm_df['days_delivery'].max(),
            'supplier_rating': norm_df['supplier_rating'].min(),
            'total_cost': norm_df['total_cost'].max()
        })

        # 5. Calculate euclidean distances from PIS and NIS
        dist_PIS = np.sqrt(((norm_df - PIS) ** 2).sum(axis=1))
        dist_NIS = np.sqrt(((norm_df - NIS) ** 2).sum(axis=1))

        # 6. Calculate relative closeness
        closeness = dist_NIS / (dist_PIS + dist_NIS)
        df['closeness'] = closeness
        norm_df['closeness'] = closeness

        # 7. Rank the alternatives based on closeness values
        df['rank'] = df['closeness'].rank(ascending=False)
        norm_df['rank'] = norm_df['closeness'].rank(ascending=False)

        # Sort the dataframes by rank
        df = df.sort_values(by='rank')
        norm_df = norm_df.sort_values(by='rank')

        df_json = df.to_json(orient='records')

        # Create the radar chart
        criteria = ['unit_price', 'days_delivery', 'supplier_rating', 'total_cost']
        norm_values = norm_df.values.tolist()
        alternative_names = list(norm_df['rank'])
        fig = go.Figure()
        for name, values in zip(alternative_names, norm_values):
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=criteria,
                fill='toself',
                name=name
            ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                )),
            showlegend=True,
            title='Multi-Criteria Evaluation of Bids: Radar Chart Ranking'
        )
        radar_plot_json = pio.to_json(fig)

        # Create a parallel coordinates plot
        fig = px.parallel_coordinates(df, color='rank', color_continuous_scale=px.colors.sequential.Viridis,
                                    labels={'rank': 'Rank'},
                                    dimensions=['unit_price', 'days_delivery', 'supplier_rating', 'total_cost'])
        fig.update_layout(
            title="Multi-Criteria Evaluation: Parallel Coordinates of Bids Ranking",
            title_x=0.5,
            title_y=0.05
        )
        parallel_plot_json = pio.to_json(fig)

        response_data = {
            'dataframe': df_json,
            'radar_plot': radar_plot_json,
            'parallel_plot': parallel_plot_json
        }
        return Response(response_data, content_type='application/json')
        

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
    ]

    return Response(routes)
