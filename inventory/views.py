import io
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
import pandas as pd
from pmdarima import auto_arima
import plotly.graph_objs as go
import plotly.io as pio
from statsmodels.tsa.seasonal import seasonal_decompose
from accounts.permissions import IsProcurementOfficer
from .models import Inventory, HistoricalInventory
from .serializers import InventorySerializer, HistoricalInventorySerializer


class InventoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventorySerializer

    def get_queryset(self):
        return Inventory.objects.filter(procurement_officer=self.request.user)


class InventoryCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    def perform_create(self, serializer):
        serializer.save(procurement_officer=self.request.user)


class InventoryRetrieveView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventorySerializer

    def get_queryset(self):
        return Inventory.objects.filter(procurement_officer=self.request.user)


class InventoryUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventorySerializer

    def get_queryset(self):
        return Inventory.objects.filter(procurement_officer=self.request.user)


class InventoryDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = InventorySerializer

    def get_queryset(self):
        return Inventory.objects.filter(procurement_officer=self.request.user)


class HistoricalInventoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = HistoricalInventorySerializer

    def get_queryset(self):
        inventory_id = self.kwargs.get("inventory_id")

        inventory = get_object_or_404(
            Inventory, id=inventory_id, procurement_officer=self.request.user
        )

        return HistoricalInventory.objects.filter(inventory=inventory)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsProcurementOfficer])
def arima_forecast(request, inventory_id):
    if request.method == "GET":
        historical_inventory = HistoricalInventory.objects.filter(inventory_id=inventory_id)
        if not historical_inventory.exists():
            return JsonResponse({'error': 'No historical inventory data found for the specified inventory_id'}, status=404)

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
            return JsonResponse({'error': 'Insufficient data for forecasting. Minimum 24 months of data required.'}, status=400)
        elif len(monthly_demand) > 60:
            monthly_demand = monthly_demand[-60:]  # Consider only the latest 60 months of data

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

        trace1 = go.Scatter(x=monthly_demand.index, y=monthly_demand['demand'], mode='lines', name='Original Data')
        forecast_dates = pd.date_range(start=monthly_demand.index[-1], periods=13, freq='M')[1:]  # Next 12 months
        trace2 = go.Scatter(x=forecast_dates, y=forecast_results, mode='lines', name='Forecast Data')
        layout = go.Layout(title='Demand Forecast', xaxis=dict(title='Date'), yaxis=dict(title='Demand'), xaxis_rangeslider_visible=True)
        fig = go.Figure(data=[trace1, trace2], layout=layout)
        graph_json = pio.to_json(fig)

        forecast_data = {
            'forecast': list(forecast_results),
            'annual_forecast': sum(forecast_results),
            'decomposed': decomposed_json,
            'graph': graph_json
        }

        return JsonResponse(forecast_data)

    elif request.method == "POST":
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)

        try:
            df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        df.columns = ['datetime', 'demand']

        df['datetime'] = pd.to_datetime(df['datetime'])

        # Resample the data to monthly frequency
        monthly_demand = df.resample('M').sum()

        # Check if there is enough data for forecasting (minimum 24 months, maximum 60 months)
        if len(monthly_demand) < 24:
            return JsonResponse({'error': 'Insufficient data for forecasting. Minimum 24 months of data required.'}, status=400)
        elif len(monthly_demand) > 60:
            monthly_demand = monthly_demand[-60:]  # Consider only the latest 60 months of data

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

        trace1 = go.Scatter(x=monthly_demand.index, y=monthly_demand['demand'], mode='lines', name='Original Data')
        forecast_dates = pd.date_range(start=monthly_demand.index[-1], periods=13, freq='M')[1:]  # Next 12 months
        trace2 = go.Scatter(x=forecast_dates, y=forecast_results, mode='lines', name='Forecast Data')
        layout = go.Layout(title='Demand Forecast', xaxis=dict(title='Date'), yaxis=dict(title='Demand'), xaxis_rangeslider_visible=True)
        fig = go.Figure(data=[trace1, trace2], layout=layout)
        graph_json = pio.to_json(fig)

        forecast_data = {
            'forecast': list(forecast_results),
            'annual_forecast': sum(forecast_results),
            'decomposed': decomposed_json,
            'graph': graph_json
        }

        return JsonResponse(forecast_data)


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
        "/forecast/<int:inventory_id>"
    ]

    return Response(routes)
