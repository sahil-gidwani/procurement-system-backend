import io
import math
from scipy.stats import norm
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema
import pandas as pd
import numpy as np
from pmdarima import auto_arima
import plotly.graph_objs as go
import plotly.io as pio
from statsmodels.tsa.seasonal import seasonal_decompose
from accounts.permissions import IsProcurementOfficer
from .models import Inventory, HistoricalInventory, OptimizedInventory
from .serializers import InventorySerializer, HistoricalInventorySerializer, OptimizedInventorySerializer


class BaseInventoryAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventorySerializer

    def get_queryset(self):
        return Inventory.objects.filter(procurement_officer=self.request.user)


class InventoryListView(BaseInventoryAPIView, generics.ListAPIView):
    pass


class InventoryCreateView(BaseInventoryAPIView, generics.CreateAPIView):
    queryset = Inventory.objects.all()

    def perform_create(self, serializer):
        serializer.save(procurement_officer=self.request.user)


class InventoryRetrieveView(BaseInventoryAPIView, generics.RetrieveAPIView):
    pass


class InventoryUpdateView(BaseInventoryAPIView, generics.UpdateAPIView):
    pass


class InventoryDeleteView(BaseInventoryAPIView, generics.DestroyAPIView):
    pass


class HistoricalInventoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = HistoricalInventorySerializer

    def get_queryset(self):
        inventory_id = self.kwargs.get("inventory_id")

        inventory = get_object_or_404(
            Inventory, id=inventory_id, procurement_officer=self.request.user
        )

        return HistoricalInventory.objects.filter(inventory=inventory)


def calculate_auto_arima(monthly_demand):
    decomposed = seasonal_decompose(monthly_demand['demand'])
    data = monthly_demand['demand']
    trend = decomposed.trend
    seasonal = decomposed.seasonal
    residual = decomposed.resid
    data_trace = go.Scatter(x=monthly_demand.index, y=data, mode='lines', name='Data')
    trend_trace = go.Scatter(x=monthly_demand.index, y=trend, mode='lines', name='Trend')
    seasonal_trace = go.Scatter(x=monthly_demand.index, y=seasonal, mode='lines', name='Seasonal')
    residual_trace = go.Scatter(x=monthly_demand.index, y=residual, mode='lines', name='Residual')
    layout = go.Layout(title='Decomposed Components',
                    xaxis=dict(title='Date'),
                    yaxis=dict(title='Value'),
                    xaxis_rangeslider_visible=True)
    fig = go.Figure(data=[data_trace, trend_trace, seasonal_trace, residual_trace], layout=layout)
    decomposed_json = pio.to_json(fig)

    model = auto_arima(monthly_demand['demand'], seasonal=True, m=12, test='adf', maxiter=100, max_order=None, d=None,
                        error_action='ignore', suppress_warnings=True, stepwise=True, trace=True)

    forecast_results = model.predict(n_periods=12, return_conf_int=False)

    trace1 = go.Scatter(x=monthly_demand.index, y=monthly_demand['demand'], mode='lines+markers', name='Original Data')
    forecast_dates = pd.date_range(start=monthly_demand.index[-1], periods=13, freq='M')[1:]  # Next 12 months
    trace2 = go.Scatter(x=forecast_dates, y=forecast_results, mode='lines+markers', name='Forecast Data')
    layout = go.Layout(title='Demand Forecast', xaxis=dict(title='Date'), yaxis=dict(title='Demand'), xaxis_rangeslider_visible=True)
    fig = go.Figure(data=[trace1, trace2], layout=layout)
    graph_json = pio.to_json(fig)

    forecast_data = {
        'decomposed': decomposed_json,
        'forecast': list(forecast_results),
        'annual_forecast': sum(forecast_results),
        'graph': graph_json
    }
    return forecast_data


class ARIMAForecastAPIView(APIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]

    def get(self, request, inventory_id):
        historical_inventory = HistoricalInventory.objects.filter(inventory_id=inventory_id, inventory__procurement_officer=request.user)
        if not historical_inventory.exists():
            return JsonResponse({'error': 'No historical inventory data found for the specified inventory_id'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            'datetime': [item.datetime for item in historical_inventory],
            'demand': [item.demand for item in historical_inventory],
            'stock_quantity': [item.stock_quantity for item in historical_inventory]
        }
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        # Resample the data to monthly frequency
        monthly_demand = df.resample('M').sum()

        # Check if there is enough data for forecasting (minimum 24 months, maximum 60 months)
        if len(monthly_demand) < 24:
            return JsonResponse({'error': 'Insufficient data for forecasting. Minimum 24 months of data required.'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(monthly_demand) > 60:
            monthly_demand = monthly_demand[-60:]  # Consider only the latest 60 months of data

        forecast_data = calculate_auto_arima(monthly_demand)
        return JsonResponse(forecast_data)

    def post(self, request, inventory_id):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        df.columns = ['datetime', 'demand']
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        # Resample the data to monthly frequency
        monthly_demand = df.resample('M').sum()

        # Check if there is enough data for forecasting (minimum 24 months, maximum 60 months)
        if len(monthly_demand) < 24:
            return JsonResponse({'error': 'Insufficient data for forecasting. Minimum 24 months of data required.'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(monthly_demand) > 60:
            monthly_demand = monthly_demand[-60:]  # Consider only the latest 60 months of data

        forecast_data = calculate_auto_arima(monthly_demand)
        return JsonResponse(forecast_data)


def calculate_eoq_classical(demand, ordering_cost, holding_cost):
    eoq = np.sqrt((2 * demand * ordering_cost) / holding_cost)
    return eoq


def calculate_safety_stock_reorder_point(demand, lead_time, service_level):
    demand_per_day = demand / 365
    lead_time_demand = demand_per_day * lead_time
    z_score = norm.ppf(service_level + (1 - service_level) / 2)
    safety_stock = z_score * math.sqrt(lead_time * demand_per_day * demand_per_day)
    reorder_point = lead_time_demand + safety_stock
    return safety_stock, reorder_point


def calculate_eoq_with_rop(demand, ordering_cost, holding_cost, lead_time, service_level):
    _, reorder_point = calculate_safety_stock_reorder_point(demand, lead_time, service_level)
    eoq_with_rop = math.sqrt((2 * demand * ordering_cost) * (reorder_point) / holding_cost)
    return eoq_with_rop


def calculate_eoq_perishable(demand, ordering_cost, holding_cost, shelf_life):
    demand_per_day = demand / 365
    eoq_perishable = math.sqrt((2 * demand_per_day * ordering_cost) * shelf_life / holding_cost)
    return eoq_perishable


def calculate_eoq_limited_storage(demand, ordering_cost, holding_cost, storage_capacity):
    eoq = math.sqrt((2 * demand * ordering_cost) / holding_cost)
    eoq_limited_storage = min(eoq, storage_capacity)
    return eoq_limited_storage


class OptimizedInventoryCreateAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = OptimizedInventorySerializer

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        demand = validated_data['demand']
        ordering_cost = validated_data['ordering_cost']
        holding_cost = validated_data['holding_cost']
        lead_time = validated_data.get('lead_time')
        service_level = validated_data.get('service_level')
        shelf_life = validated_data.get('shelf_life')
        storage_limit = validated_data.get('storage_limit')
        inventory_id = self.kwargs.get('inventory_id')

        inventory = get_object_or_404(Inventory, id=inventory_id)
        if inventory.procurement_officer != self.request.user:
            raise PermissionDenied("You don't have permission to create OptimizedInventory for this inventory.")

        if lead_time is not None and service_level is not None:
            safety_stock, reorder_point = calculate_safety_stock_reorder_point(demand, lead_time, service_level)
        else:
            safety_stock, reorder_point = None, None

        if all(param is None for param in [lead_time, service_level, shelf_life, storage_limit]):
            eoq = calculate_eoq_classical(demand, ordering_cost, holding_cost)
        elif lead_time is not None and service_level is not None:
            eoq = calculate_eoq_with_rop(demand, ordering_cost, holding_cost, lead_time, service_level)
        elif shelf_life is not None:
            eoq = calculate_eoq_perishable(demand, ordering_cost, holding_cost, shelf_life)
        elif storage_limit is not None:
            eoq = calculate_eoq_limited_storage(demand, ordering_cost, holding_cost, storage_limit)
        else:
            eoq = None

        serializer.save(
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            eoq=eoq,
            inventory_id=inventory_id
        )
    

class OptimizedInventoryUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = OptimizedInventorySerializer

    def update(self, request, *args, **kwargs):
        inventory_id = self.kwargs.get('inventory_id')

        try:
            optimized_inventory = OptimizedInventory.objects.get(inventory_id=inventory_id)
        except OptimizedInventory.DoesNotExist:
            return Response({"detail": "OptimizedInventory not found"}, status=status.HTTP_404_NOT_FOUND)

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(optimized_inventory, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        inventory = get_object_or_404(Inventory, id=inventory_id)
        if inventory.procurement_officer != self.request.user:
            raise PermissionDenied("You don't have permission to update OptimizedInventory for this inventory.")
        
        self.perform_update(serializer)

        return Response(serializer.data)

    def perform_update(self, serializer):
        validated_data = serializer.validated_data
        demand = validated_data.get('demand')
        ordering_cost = validated_data.get('ordering_cost')
        holding_cost = validated_data.get('holding_cost')
        lead_time = validated_data.get('lead_time')
        service_level = validated_data.get('service_level')
        shelf_life = validated_data.get('shelf_life')
        storage_limit = validated_data.get('storage_limit')

        # if demand is None:
        #     demand = serializer.instance.demand
        # if ordering_cost is None:
        #     ordering_cost = serializer.instance.ordering_cost
        # if holding_cost is None:
        #     holding_cost = serializer.instance.holding_cost
        # if lead_time is None:
        #     lead_time = serializer.instance.lead_time
        # if service_level is None:
        #     service_level = serializer.instance.service_level
        # if shelf_life is None:
        #     shelf_life = serializer.instance.shelf_life
        # if storage_limit is None:
        #     storage_limit = serializer.instance.storage_limit

        if lead_time is not None and service_level is not None:
            safety_stock, reorder_point = calculate_safety_stock_reorder_point(demand, lead_time, service_level)
        else:
            safety_stock, reorder_point = None, None

        if all(param is None for param in [lead_time, service_level, shelf_life, storage_limit]):
            eoq = calculate_eoq_classical(demand, ordering_cost, holding_cost)
        elif lead_time is not None and service_level is not None:
            eoq = calculate_eoq_with_rop(demand, ordering_cost, holding_cost, lead_time, service_level)
        elif shelf_life is not None:
            eoq = calculate_eoq_perishable(demand, ordering_cost, holding_cost, shelf_life)
        elif storage_limit is not None:
            eoq = calculate_eoq_limited_storage(demand, ordering_cost, holding_cost, storage_limit)
        else:
            eoq = None

        serializer.save(
            safety_stock=safety_stock,
            reorder_point=reorder_point,
            eoq=eoq
        )


class BaseOptimizedInventoryAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = OptimizedInventorySerializer
    lookup_field = 'inventory_id' 

    def get_queryset(self):
        inventory_id = self.kwargs.get("inventory_id")

        inventory = get_object_or_404(
            Inventory, id=inventory_id, procurement_officer=self.request.user
        )

        return OptimizedInventory.objects.filter(inventory=inventory)


class OptimizedInventoryRetrieveAPIView(BaseOptimizedInventoryAPIView, generics.RetrieveAPIView):
    pass


class OptimizedInventoryDestroyAPIView(BaseOptimizedInventoryAPIView, generics.DestroyAPIView):
    pass


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        "/list",
        "/create",
        "/<int:pk>",
        "/<int:pk>/update",
        "/<int:pk>/delete",
        "/historical/<int:inventory_id>/list",
        "/forecast/<int:inventory_id>",
        "/optimize/<int:inventory_id>",
        "/optimize/<int:inventory_id>/create",
        "/optimize/<int:inventory_id>/update",
        "/optimize/<int:inventory_id>/delete",
    ]

    return Response(routes)
