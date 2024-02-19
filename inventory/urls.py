from django.urls import path
from . import views

urlpatterns = [
    path("", views.getRoutes, name="inventory_routes"),
    path("list/", views.InventoryListView.as_view(), name="inventory_list"),
    path("create/", views.InventoryCreateView.as_view(), name="inventory_create"),
    path("<int:pk>/", views.InventoryRetrieveView.as_view(), name="inventory_retrieve"),
    path(
        "<int:pk>/update/", views.InventoryUpdateView.as_view(), name="inventory_update"
    ),
    path(
        "<int:pk>/delete/", views.InventoryDeleteView.as_view(), name="inventory_delete"
    ),
    path(
        "historical/<int:inventory_id>/list/",
        views.HistoricalInventoryListView.as_view(),
        name="historical_inventory_list",
    ),
    path(
        "forecast/<int:inventory_id>/",
        views.ARIMAForecastAPIView.as_view(),
        name="arima_forecast",
    ),
    path(
        "optimize/<int:inventory_id>/",
        views.OptimizedInventoryRetrieveAPIView.as_view(),
        name="optimized_inventory_retrieve",
    ),
    path(
        "optimize/<int:inventory_id>/create/",
        views.OptimizedInventoryCreateAPIView.as_view(),
        name="optimized_inventory_create",
    ),
    path(
        "optimize/<int:inventory_id>/update/",
        views.OptimizedInventoryUpdateAPIView.as_view(),
        name="optimized_inventory_update"
    ),
    path(
        "optimize/<int:inventory_id>/delete/",
        views.OptimizedInventoryDestroyAPIView.as_view(),
        name="optimized_inventory_delete"
    ),
]
