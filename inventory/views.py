from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
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
        inventory_id = self.kwargs.get('inventory_id')

        inventory = get_object_or_404(Inventory, id=inventory_id, procurement_officer=self.request.user)

        return HistoricalInventory.objects.filter(inventory=inventory)

@api_view(['GET'])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        '/list',
        '/create',
        '/<int:pk>',
        '/<int:pk>/update',
        '/<int:pk>/delete',
        '/historical/list/<int:inventory_id>',
    ]

    return Response(routes)
