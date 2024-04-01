from django.db.models import F
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from .serializers import AdminDashboardSerializer, ProcurementOfficerDashboardSerializer, VendorDashboardSerializer
from accounts.models import User, Vendor
from inventory.models import Inventory
from purchase.models import PurchaseRequisition, SupplierBid, PurchaseOrder
from accounts.permissions import IsProcurementOfficer, IsVendor


@method_decorator(cache_page(60 * 15), name="dispatch")
class AdminDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AdminDashboardSerializer

    def get(self, request):
        # * Users Analysis
        users = User.objects.all()

        # Get the total number of users
        total_users = users.count()

        # Users by role
        users_by_role = users.values("user_role").annotate(
            count=F("id")).order_by("user_role")

        users_by_role_plot = go.Figure()
        users_by_role_plot.add_trace(go.Pie(
            labels=[item["user_role"] for item in users_by_role],
            values=[item["count"] for item in users_by_role]
        ))
        users_by_role_plot.update_layout(title="Users by Role")
        users_by_role_plot = pio.to_json(users_by_role_plot)

        # User Registration over time (monthly)
        user_registration_over_time = users.annotate(
            month=ExtractMonth("date_joined")
        ).values("month").annotate(count=F("id")).order_by("month")

        user_registration_over_time_plot = go.Figure()
        user_registration_over_time_plot.add_trace(go.Bar(
            x=[item["month"] for item in user_registration_over_time],
            y=[item["count"] for item in user_registration_over_time],
            text=[item["count"] for item in user_registration_over_time],
            textposition="outside",
            marker=dict(color=[item["count"]
                        for item in user_registration_over_time])
        ))
        user_registration_over_time_plot.update_layout(
            title="User Registration Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Users",
            coloraxis_colorbar=dict(title="Number of Users")
        )
        user_registration_over_time_plot = pio.to_json(
            user_registration_over_time_plot)

        # * Vendor Analysis
        vendors = Vendor.objects.all()

        # Vendors by Vendor Type
        vendors_by_vendor_type = vendors.values("vendor_type").annotate(
            count=F("id")).order_by("vendor_type")

        vendors_by_vendor_type_plot = go.Figure()
        vendors_by_vendor_type_plot.add_trace(go.Pie(
            labels=[item["vendor_type"] for item in vendors_by_vendor_type],
            values=[item["count"] for item in vendors_by_vendor_type]
        ))
        vendors_by_vendor_type_plot.update_layout(
            title="Vendors by Vendor Type")
        vendors_by_vendor_type_plot = pio.to_json(vendors_by_vendor_type_plot)

        # Vendor Rating Distribution
        vendor_rating_distribution = vendors.values("vendor_rating")
        vendor_rating_distribution = pd.DataFrame(vendor_rating_distribution)
        vendor_rating_distribution = vendor_rating_distribution.groupby(
            "vendor_rating").size().reset_index(name="count")

        vendor_rating_distribution_plot = go.Figure()
        vendor_rating_distribution_plot.add_trace(go.Histogram(
            x=vendor_rating_distribution["vendor_rating"],
            y=vendor_rating_distribution["count"]
        ))
        vendor_rating_distribution_plot.update_layout(
            title="Vendor Rating Distribution")
        vendor_rating_distribution_plot = pio.to_json(
            vendor_rating_distribution_plot)

        # Serializing the data
        serializer = AdminDashboardSerializer(data={
            "total_users": total_users,
            "users_by_role": users_by_role_plot,
            "user_registration_over_time": user_registration_over_time_plot,
            "vendors_by_vendor_type": vendors_by_vendor_type_plot,
            "vendor_rating_distribution": vendor_rating_distribution_plot
        })

        # Validating and returning the serialized data
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, content_type="application/json")


@method_decorator(cache_page(60 * 15), name="dispatch")
class ProcurementOfficerDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsProcurementOfficer]
    serializer_class = ProcurementOfficerDashboardSerializer

    def get(self, request):
        user = request.user

        # * Inventory Analysis
        inventory_items = Inventory.objects.filter(procurement_officer=user)

        # Get the total number of inventory items
        total_inventory_items = inventory_items.count()

        # Top items by stock quantity
        top_items_stock_quantity = inventory_items.order_by(
            "-stock_quantity")[:5]

        top_items_stock_quantity_plot = go.Figure()
        top_items_stock_quantity_plot.add_trace(go.Bar(
            x=[item.item_name for item in top_items_stock_quantity],
            y=[item.stock_quantity for item in top_items_stock_quantity],
            text=[item.stock_quantity for item in top_items_stock_quantity],
            textposition="outside",
            marker=dict(
                color=[item.stock_quantity for item in top_items_stock_quantity])
        ))
        top_items_stock_quantity_plot.update_layout(
            title="Top Items by Stock Quantity",
            xaxis_title="Item Name",
            yaxis_title="Stock Quantity",
            coloraxis_colorbar=dict(title="Stock Quantity")
        )
        top_items_stock_quantity_plot = pio.to_json(
            top_items_stock_quantity_plot)

        # Top items by unit price
        top_items_unit_price = inventory_items.order_by("-unit_price")[:5]

        top_items_unit_price_plot = go.Figure()
        top_items_unit_price_plot.add_trace(go.Bar(
            x=[item.item_name for item in top_items_unit_price],
            y=[item.unit_price for item in top_items_unit_price],
            text=[f"${item.unit_price}" for item in top_items_unit_price],
            textposition="outside",
            marker=dict(
                color=[item.unit_price for item in top_items_unit_price])
        ))
        top_items_unit_price_plot.update_layout(
            title="Top Items by Unit Price",
            xaxis_title="Item Name",
            yaxis_title="Unit Price",
            coloraxis_colorbar=dict(title="Unit Price")
        )
        top_items_unit_price_plot = pio.to_json(top_items_unit_price_plot)

        # Top items by total price
        top_items_total_price = inventory_items.annotate(total_price=F(
            'stock_quantity') * F('unit_price')).order_by("-total_price")[:5]

        top_items_total_price_plot = go.Figure()
        top_items_total_price_plot.add_trace(go.Bar(
            x=[item.item_name for item in top_items_total_price],
            y=[item.stock_quantity * item.unit_price for item in top_items_total_price],
            text=[
                f"${item.stock_quantity * item.unit_price}" for item in top_items_total_price],
            textposition="outside",
            marker=dict(
                color=[item.stock_quantity for item in top_items_total_price])
        ))
        top_items_total_price_plot.update_layout(
            title="Top Items by Total Price",
            xaxis_title="Item Name",
            yaxis_title="Total Price",
            coloraxis_colorbar=dict(title="Stock Quantity")
        )
        top_items_total_price_plot = pio.to_json(top_items_total_price_plot)

        # Inventory Items added over time (monthly)
        inventory_items_added = inventory_items.annotate(
            month=ExtractMonth('date_added')
        ).values("month").annotate(count=Count('id')).order_by("month")

        inventory_items_added_plot = go.Figure()
        inventory_items_added_plot.add_trace(go.Bar(
            x=[item["month"] for item in inventory_items_added],
            y=[item["count"] for item in inventory_items_added],
            text=[item["count"] for item in inventory_items_added],
            textposition="outside",
            marker=dict(color=[item["count"]
                        for item in inventory_items_added])
        ))
        inventory_items_added_plot.update_layout(
            title="Inventory Items Added Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Items",
            coloraxis_colorbar=dict(title="Number of Items")
        )
        inventory_items_added_plot = pio.to_json(inventory_items_added_plot)

        # Inventory Age Analysis
        inventory_age = pd.DataFrame(list(inventory_items.values(
            "item_name", "stock_quantity", "date_added", "last_updated")))
        inventory_age["date_added"] = pd.to_datetime(
            inventory_age["date_added"])
        inventory_age["last_updated"] = pd.to_datetime(
            inventory_age["last_updated"])
        inventory_age["age"] = (
            inventory_age["last_updated"] - inventory_age["date_added"]).dt.days
        inventory_age = inventory_age[["item_name", "stock_quantity", "age"]]
        inventory_age = inventory_age.sort_values("age", ascending=False)

        fig = px.bar(inventory_age, x="item_name", y="age",
                     color="stock_quantity", title="Inventory Age Analysis")
        fig.update_layout(
            xaxis_title="Item Name",
            yaxis_title="Age (Days)",
            coloraxis_colorbar=dict(title="Stock Quantity")
        )
        inventory_age_plot = pio.to_json(fig)

        # Stock Quantity Distribution over Locations
        stock_quantity_distribution = inventory_items.values(
            "location", "stock_quantity")
        stock_quantity_distribution = pd.DataFrame(stock_quantity_distribution)
        stock_quantity_distribution = stock_quantity_distribution.groupby(
            "location").agg({"stock_quantity": "sum"}).reset_index()

        stock_quantity_distribution_plot = go.Figure()
        stock_quantity_distribution_plot.add_trace(go.Pie(
            labels=stock_quantity_distribution["location"],
            values=stock_quantity_distribution["stock_quantity"]
        ))
        stock_quantity_distribution_plot.update_layout(
            title="Stock Quantity Distribution over Locations")
        stock_quantity_distribution_plot = pio.to_json(
            stock_quantity_distribution_plot)

        # * Purchase Requisitions Analysis
        purchase_requisitions = PurchaseRequisition.objects.filter(
            inventory__procurement_officer=user)

        # Get the total number of purchase requisitions
        total_purchase_requisitions = purchase_requisitions.count()

        # Purchase Requisitions by status
        purchase_requisitions_by_status = purchase_requisitions.values(
            "status").annotate(count=F("id")).order_by("status")

        purchase_requisitions_by_status_plot = go.Figure()
        purchase_requisitions_by_status_plot.add_trace(go.Pie(
            labels=[item["status"]
                    for item in purchase_requisitions_by_status],
            values=[item["count"] for item in purchase_requisitions_by_status]
        ))
        purchase_requisitions_by_status_plot.update_layout(
            title="Purchase Requisitions by Status")
        purchase_requisitions_by_status_plot = pio.to_json(
            purchase_requisitions_by_status_plot)

        # Purchase Requisitions over time (monthly)
        purchase_requisitions_over_time = purchase_requisitions.annotate(
            month=ExtractMonth('date_created')
        ).values("month").annotate(count=Count('id')).order_by("month")

        purchase_requisitions_over_time_plot = go.Figure()
        purchase_requisitions_over_time_plot.add_trace(go.Bar(
            x=[item["month"] for item in purchase_requisitions_over_time],
            y=[item["count"] for item in purchase_requisitions_over_time],
            text=[item["count"] for item in purchase_requisitions_over_time],
            textposition="outside",
            marker=dict(color=[item["count"]
                        for item in purchase_requisitions_over_time])
        ))
        purchase_requisitions_over_time_plot.update_layout(
            title="Purchase Requisitions Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Requisitions",
            coloraxis_colorbar=dict(title="Number of Requisitions")
        )
        purchase_requisitions_over_time_plot = pio.to_json(
            purchase_requisitions_over_time_plot)

        # Purchase Requisitions Age Analysis
        purchase_requisitions_age = pd.DataFrame(list(purchase_requisitions.values(
            "inventory__item_name", "quantity_requested", "date_created", "last_updated")))
        purchase_requisitions_age["date_created"] = pd.to_datetime(
            purchase_requisitions_age["date_created"])
        purchase_requisitions_age["last_updated"] = pd.to_datetime(
            purchase_requisitions_age["last_updated"])
        purchase_requisitions_age["age"] = (
            purchase_requisitions_age["last_updated"] - purchase_requisitions_age["date_created"]).dt.days
        purchase_requisitions_age = purchase_requisitions_age[[
            "inventory__item_name", "quantity_requested", "age"]]
        purchase_requisitions_age = purchase_requisitions_age.sort_values(
            "age", ascending=False)

        fig = px.bar(purchase_requisitions_age, x="inventory__item_name", y="age",
                     color="quantity_requested", title="Purchase Requisitions Age Analysis")
        fig.update_layout(
            xaxis_title="Item Name",
            yaxis_title="Age (Days)",
            coloraxis_colorbar=dict(title="Quantity")
        )
        purchase_requisitions_age_plot = pio.to_json(fig)

        # Quantity Requested Distribution over Locations
        quantity_requested_distribution = purchase_requisitions.values(
            "inventory__location", "quantity_requested")
        quantity_requested_distribution = pd.DataFrame(
            quantity_requested_distribution)
        quantity_requested_distribution = quantity_requested_distribution.groupby(
            "inventory__location").agg({"quantity_requested": "sum"}).reset_index()

        quantity_requested_distribution_plot = go.Figure()
        quantity_requested_distribution_plot.add_trace(go.Pie(
            labels=quantity_requested_distribution["inventory__location"],
            values=quantity_requested_distribution["quantity_requested"]
        ))
        quantity_requested_distribution_plot.update_layout(
            title="Quantity Requested Distribution over Locations")
        quantity_requested_distribution_plot = pio.to_json(
            quantity_requested_distribution_plot)

        # Serializing the data
        serializer = ProcurementOfficerDashboardSerializer(data={
            "total_inventory_items": total_inventory_items,
            "top_items_stock_quantity": top_items_stock_quantity_plot,
            "top_items_unit_price": top_items_unit_price_plot,
            "top_items_total_price": top_items_total_price_plot,
            "inventory_items_added": inventory_items_added_plot,
            "inventory_age": inventory_age_plot,
            "stock_quantity_distribution": stock_quantity_distribution_plot,
            "total_purchase_requisitions": total_purchase_requisitions,
            "purchase_requisitions_by_status": purchase_requisitions_by_status_plot,
            "purchase_requisitions_over_time": purchase_requisitions_over_time_plot,
            "purchase_requisitions_age": purchase_requisitions_age_plot,
            "quantity_requested_distribution": quantity_requested_distribution_plot
        })

        # Validating and returning the serialized data
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, content_type="application/json")


@method_decorator(cache_page(60 * 15), name="dispatch")
class VendorDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = VendorDashboardSerializer

    def get(self, request):
        user = request.user

        # * Supplier Bid Analysis
        supplier_bids = SupplierBid.objects.filter(supplier=user)

        # Get the total number of supplier bids
        total_supplier_bids = supplier_bids.count()

        # Top bids by bid amount
        top_bids_bid_amount = supplier_bids.annotate(bid_amount=F(
            "unit_price") * F("quantity_fulfilled")).order_by("-bid_amount")[:5]

        top_bids_bid_amount_plot = go.Figure()
        top_bids_bid_amount_plot.add_trace(go.Bar(
            x=[item.id for item in top_bids_bid_amount],
            y=[item.bid_amount for item in top_bids_bid_amount],
            text=[f"${item.bid_amount}" for item in top_bids_bid_amount],
            textposition="outside",
            marker=dict(
                color=[item.bid_amount for item in top_bids_bid_amount])
        ))
        top_bids_bid_amount_plot.update_layout(
            title="Top Bids by Bid Amount",
            xaxis_title="Bid ID",
            yaxis_title="Bid Amount",
            coloraxis_colorbar=dict(title="Bid Amount")
        )
        top_bids_bid_amount_plot = pio.to_json(top_bids_bid_amount_plot)

        # Supplier Bids by status
        supplier_bids_by_status = supplier_bids.values(
            "status").annotate(count=F("id")).order_by("status")

        supplier_bids_by_status_plot = go.Figure()
        supplier_bids_by_status_plot.add_trace(go.Pie(
            labels=[item["status"] for item in supplier_bids_by_status],
            values=[item["count"] for item in supplier_bids_by_status]
        ))
        supplier_bids_by_status_plot.update_layout(
            title="Supplier Bids by Status")
        supplier_bids_by_status_plot = pio.to_json(
            supplier_bids_by_status_plot)

        # Supplier Bids over time (monthly)
        supplier_bids_over_time = supplier_bids.annotate(
            month=ExtractMonth("date_submitted")
        ).values("month").annotate(count=F("id")).order_by("month")

        supplier_bids_over_time_plot = go.Figure()
        supplier_bids_over_time_plot.add_trace(go.Bar(
            x=[item["month"] for item in supplier_bids_over_time],
            y=[item["count"] for item in supplier_bids_over_time],
            text=[item["count"] for item in supplier_bids_over_time],
            textposition="outside",
            marker=dict(color=[item["count"]
                        for item in supplier_bids_over_time])
        ))
        supplier_bids_over_time_plot.update_layout(
            title="Supplier Bids Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Bids",
            coloraxis_colorbar=dict(title="Number of Bids")
        )
        supplier_bids_over_time_plot = pio.to_json(
            supplier_bids_over_time_plot)

        # * Purchase Orders Analysis
        purchase_orders = PurchaseOrder.objects.filter(bid__supplier=user)

        # Get the total number of purchase orders
        total_purchase_orders = purchase_orders.count()

        # Top orders by order amount
        top_orders_order_amount = purchase_orders.annotate(order_amount=F(
            "bid__unit_price") * F("bid__quantity_fulfilled")).order_by("-order_amount")[:5]

        top_orders_order_amount_plot = go.Figure()
        top_orders_order_amount_plot.add_trace(go.Bar(
            x=[item.order_id for item in top_orders_order_amount],
            y=[item.order_amount for item in top_orders_order_amount],
            text=[f"${item.order_amount}" for item in top_orders_order_amount],
            textposition="outside",
            marker=dict(
                color=[item.order_amount for item in top_orders_order_amount])
        ))
        top_orders_order_amount_plot.update_layout(
            title="Top Orders by Order Amount",
            xaxis_title="Order ID",
            yaxis_title="Order Amount",
            coloraxis_colorbar=dict(title="Order Amount")
        )
        top_orders_order_amount_plot = pio.to_json(
            top_orders_order_amount_plot)

        # Purchase Orders by status
        purchase_orders_by_status = purchase_orders.values(
            "status").annotate(count=F("id")).order_by("status")

        purchase_orders_by_status_plot = go.Figure()
        purchase_orders_by_status_plot.add_trace(go.Pie(
            labels=[item["status"] for item in purchase_orders_by_status],
            values=[item["count"] for item in purchase_orders_by_status]
        ))
        purchase_orders_by_status_plot.update_layout(
            title="Purchase Orders by Status")
        purchase_orders_by_status_plot = pio.to_json(
            purchase_orders_by_status_plot)

        # Purchase Orders over time (monthly)
        purchase_orders_over_time = purchase_orders.annotate(
            month=ExtractMonth("date_ordered")
        ).values("month").annotate(count=F("id")).order_by("month")

        purchase_orders_over_time_plot = go.Figure()
        purchase_orders_over_time_plot.add_trace(go.Bar(
            x=[item["month"] for item in purchase_orders_over_time],
            y=[item["count"] for item in purchase_orders_over_time],
            text=[item["count"] for item in purchase_orders_over_time],
            textposition="outside",
            marker=dict(color=[item["count"]
                        for item in purchase_orders_over_time])
        ))
        purchase_orders_over_time_plot.update_layout(
            title="Purchase Orders Over Time",
            xaxis_title="Month",
            yaxis_title="Number of Orders",
            coloraxis_colorbar=dict(title="Number of Orders")
        )
        purchase_orders_over_time_plot = pio.to_json(
            purchase_orders_over_time_plot)

        # Serializing the data
        serializer = VendorDashboardSerializer(data={
            "total_supplier_bids": total_supplier_bids,
            "top_bids_bid_amount": top_bids_bid_amount_plot,
            "supplier_bids_by_status": supplier_bids_by_status_plot,
            "supplier_bids_over_time": supplier_bids_over_time_plot,
            "total_purchase_orders": total_purchase_orders,
            "top_orders_order_amount": top_orders_order_amount_plot,
            "purchase_orders_by_status": purchase_orders_by_status_plot,
            "purchase_orders_over_time": purchase_orders_over_time_plot
        })

        # Validating and returning the serialized data
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, content_type="application/json")


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        "/admin",
        "/procurement-officer",
        "/vendor"
    ]

    return Response(routes)
