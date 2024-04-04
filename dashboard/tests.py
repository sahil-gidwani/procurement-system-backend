from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, Vendor
from inventory.models import Inventory
from purchase.models import PurchaseRequisition, SupplierBid, PurchaseOrder


class SetupClass(TestCase):
    def setUp(self):
        cache.clear()

        self.client = APIClient()

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            gstin="12ABCDE2234F1Z5",
            password="testpassword",
            is_staff=True,
            is_superuser=True,
        )

        self.procurement_officer = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="procurement_officer",
            email="procurement_officer@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="procurement_officer",
        )

        self.vendor = User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="vendor",
            email="vendor@example.com",
            phone_number="9876543210",
            gstin="42ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="vendor",
        )
        Vendor.objects.create(
            user=self.vendor,
            vendor_certified=True,
            vendor_type="supplier",
        )

        self.inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        self.purchase_requisition = PurchaseRequisition.objects.create(
            requisition_number="PR-001",
            quantity_requested=50,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="medium",
            status="pending",
            inventory=self.inventory_item,
        )

        self.supplier_bid = SupplierBid.objects.create(
            quantity_fulfilled=60,
            unit_price=10.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition,
        )

        self.purchase_order = PurchaseOrder.objects.create(
            order_number="PO-001",
            status="pending",
            bid=self.supplier_bid,
        )

        self.admin_dashboard_url = reverse("admin_dashboard")
        self.procurement_officer_dashboard_url = reverse(
            "procurement_officer_dashboard"
        )
        self.vendor_dashboard_url = reverse("vendor_dashboard")


class DashboardViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_admin_dashboard_view(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_dashboard_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_dashboard_view_unauthenticated(self):
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_dashboard_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_dashboard_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.admin_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_procurement_officer_dashboard_view(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_procurement_officer_dashboard_view_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_procurement_officer_dashboard_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_procurement_officer_dashboard_view_unauthenticated(self):
        response = self.client.get(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_procurement_officer_dashboard_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_procurement_officer_dashboard_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.procurement_officer_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_vendor_dashboard_view(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_dashboard_view_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_dashboard_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_dashboard_view_unauthenticated(self):
        response = self.client.get(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vendor_dashboard_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vendor_dashboard_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.vendor_dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
