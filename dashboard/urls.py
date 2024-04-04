from django.urls import path
from . import views

urlpatterns = [
    path("", views.getRoutes, name="dashboard_routes"),
    path("admin/", views.AdminDashboardView.as_view(), name="admin_dashboard"),
    path(
        "procurement-officer/",
        views.ProcurementOfficerDashboardView.as_view(),
        name="procurement_officer_dashboard",
    ),
    path("vendor/", views.VendorDashboardView.as_view(), name="vendor_dashboard"),
]
