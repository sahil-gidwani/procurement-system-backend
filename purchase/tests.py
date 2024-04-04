from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, Vendor
from inventory.models import Inventory
from .models import PurchaseRequisition, SupplierBid, PurchaseOrder


class SetupClass(TestCase):
    def setUp(self):
        cache.clear()

        self.client = APIClient()

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

        self.procurement_officer2 = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="procurement_officer2",
            email="procurement_officer2@example.com",
            phone_number="1234567891",
            gstin="32ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="procurement_officer",
        )

        self.vendor2 = User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="vendor2",
            email="vendor2@example.com",
            phone_number="9876543211",
            gstin="62ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="vendor",
        )
        Vendor.objects.create(
            user=self.vendor2,
            vendor_certified=True,
            vendor_type="manufacturer",
        )

        self.inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        self.inventory_item2 = Inventory.objects.create(
            item_name="Test Item 2",
            description="Test Description 2",
            unit_price=15.00,
            stock_quantity=150,
            location="Test Location 2",
            procurement_officer=self.procurement_officer,
        )

        self.inventory_item3 = Inventory.objects.create(
            item_name="Test Item 3",
            description="Test Description 3",
            unit_price=20.00,
            stock_quantity=200,
            location="Test Location 3",
            procurement_officer=self.procurement_officer,
        )

        self.inventory_item4 = Inventory.objects.create(
            item_name="Test Item 4",
            description="Test Description 4",
            unit_price=25.00,
            stock_quantity=250,
            location="Test Location 4",
            procurement_officer=self.procurement_officer,
        )

        self.inventory_item5 = Inventory.objects.create(
            item_name="Test Item 5",
            description="Test Description 5",
            unit_price=30.00,
            stock_quantity=300,
            location="Test Location 5",
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

        self.purchase_requisition2 = PurchaseRequisition.objects.create(
            requisition_number="PR-002",
            quantity_requested=100,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="high",
            status="approved",
            inventory=self.inventory_item2,
        )

        self.purchase_requisition3 = PurchaseRequisition.objects.create(
            requisition_number="PR-003",
            quantity_requested=150,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="low",
            status="rejected",
            inventory=self.inventory_item3,
        )

        self.purchase_requisition_list_url = reverse(
            "purchase_requisition_list")
        self.purchase_requisition_create_url = reverse(
            "purchase_requisition_create", kwargs={'inventory_id': 4})
        self.purchase_requisition_create_existing_url = reverse(
            "purchase_requisition_create", kwargs={'inventory_id': 1})
        self.purchase_requisition_retrieve_url = reverse(
            "purchase_requisition_detail", kwargs={'pk': 1})
        self.purchase_requisition_update_url = reverse(
            "purchase_requisition_update", kwargs={'pk': 1})
        self.purchase_requisition_update_status_approved_url = reverse(
            "purchase_requisition_update", kwargs={'pk': 2})
        self.purchase_requisition_update_status_rejected_url = reverse(
            "purchase_requisition_update", kwargs={'pk': 3})
        self.purchase_requisition_delete_url = reverse(
            "purchase_requisition_delete", kwargs={'pk': 1})
        self.purchase_requisition_delete_status_approved_url = reverse(
            "purchase_requisition_delete", kwargs={'pk': 2})
        self.purchase_requisition_delete_status_rejected_url = reverse(
            "purchase_requisition_delete", kwargs={'pk': 3})
        self.purchase_requisition_vendor_list_url = reverse(
            "purchase_requisition_vendor_list")
        self.supplier_bid_list_url = reverse("supplier_bid_list")
        self.supplier_bid_create_url = reverse(
            "supplier_bid_create", kwargs={'requisition_id': 1})
        self.supplier_bid_create_requisition_status_approved_url = reverse(
            "supplier_bid_create", kwargs={'requisition_id': 2})
        self.supplier_bid_create_requisition_status_rejected_url = reverse(
            "supplier_bid_create", kwargs={'requisition_id': 3})
        self.supplier_bid_retrieve_url = reverse(
            "supplier_bid_detail", kwargs={'pk': 1})
        self.supplier_bid_update_url = reverse(
            "supplier_bid_update", kwargs={'pk': 1})
        self.supplier_bid_update_status_accepted_url = reverse(
            "supplier_bid_update", kwargs={'pk': 3})
        self.supplier_bid_update_status_rejected_url = reverse(
            "supplier_bid_update", kwargs={'pk': 4})
        self.supplier_bid_delete_url = reverse(
            "supplier_bid_delete", kwargs={'pk': 1})
        self.supplier_bid_delete_status_accepted_url = reverse(
            "supplier_bid_delete", kwargs={'pk': 3})
        self.supplier_bid_delete_status_rejected_url = reverse(
            "supplier_bid_delete", kwargs={'pk': 4})
        self.supplier_bid_procurment_officer_list_url = reverse(
            "supplier_bid_procurement_officer_list", kwargs={'requisition_id': 4})
        self.supplier_bid_procurement_officer_ranking_url = reverse(
            "supplier_bid_procurement_officer_ranking", kwargs={'requisition_id': 4})
        self.supplier_bid_procurement_officer_detail_url = reverse(
            "supplier_bid_procurement_officer_detail", kwargs={'pk': 1})
        self.supplier_bid_procurement_officer_status_url = reverse(
            "supplier_bid_procurement_officer_status", kwargs={'pk': 1})
        self.supplier_bid_procurement_officer_status_accepted_url = reverse(
            "supplier_bid_procurement_officer_status", kwargs={'pk': 3})
        self.supplier_bid_procurement_officer_status_rejected_url = reverse(
            "supplier_bid_procurement_officer_status", kwargs={'pk': 4})
        self.purchase_order_list_url = reverse("purchase_order_list")
        self.purchase_order_vendor_list_url = reverse(
            "purchase_order_vendor_list")
        self.purchase_order_vendor_status_url = reverse(
            "purchase_order_vendor_status", kwargs={'pk': 1})
        self.purchase_order_vendor_status_pending_url = reverse(
            "purchase_order_vendor_status", kwargs={'pk': 1})
        self.purchase_order_vendor_status_shipped_url = reverse(
            "purchase_order_vendor_status", kwargs={'pk': 2})
        self.purchase_order_vendor_status_delivered_url = reverse(
            "purchase_order_vendor_status", kwargs={'pk': 3})


class PurchaseRequisitionViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_purchase_requisition_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_purchase_requisition_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_requisition_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_purchase_requisition_list_view_unauthenticated(self):
        response = self.client.get(self.purchase_requisition_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.purchase_requisition_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.purchase_requisition_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_purchase_requisition_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "requisition_number": "PR-004",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["requisition_number"], "PR-004")
        purchase_requisition = PurchaseRequisition.objects.get(requisition_number="PR-004")
        self.assertEqual(purchase_requisition.status, "pending")

    def test_purchase_requisition_create_view_one_to_one_inventory(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "requisition_number": "PR-002",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_existing_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_other_inventory(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "requisition_number": "PR-004",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "requisition_number": "PR-002",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_unauthenticated(self):
        data = {
            "requisition_number": "PR-002",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "requisition_number": "PR-002",
            "quantity_requested": 20,
            "expected_delivery_date": (timezone.now() + timedelta(days=7)).date(),
            "urgency_level": "low",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.purchase_requisition_create_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "requisition_number": "PR-002",
            "quantity_requested": "invalid",
            "expected_delivery_date": "invalid",
            "urgency_level": "invalid",
        }
        response = self.client.post(self.purchase_requisition_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_retrieve_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["requisition_number"], "PR-001")

    def test_purchase_requisition_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_purchase_requisition_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_purchase_requisition_retrieve_view_unauthenticated(self):
        response = self.client.get(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.purchase_requisition_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_purchase_requisition_update_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_requested": 60,
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity_requested"], 60)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 60)
        self.assertEqual(purchase_requisition.status, "pending")

    def test_purchase_requisition_update_view_status_approved(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_requested": 150,
        }
        response = self.client.patch(self.purchase_requisition_update_status_approved_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_requisition = PurchaseRequisition.objects.get(pk=2)
        self.assertEqual(purchase_requisition.quantity_requested, 100)

    def test_purchase_requisition_update_view_status_rejected(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_requested": 200,
        }
        response = self.client.patch(self.purchase_requisition_update_status_rejected_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        purchase_requisition = PurchaseRequisition.objects.get(pk=3)
        self.assertEqual(purchase_requisition.quantity_requested, 200)
        self.assertEqual(purchase_requisition.status, "pending")

    def test_purchase_requisition_update_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "quantity_requested": 60,
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_requested": 60,
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_unauthenticated(self):
        data = {
            "quantity_requested": 60,
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "quantity_requested": 60,
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.patch(self.purchase_requisition_update_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_requested": "invalid",
            "expected_delivery_date": "invalid",
            "urgency_level": "invalid",
        }
        response = self.client.patch(self.purchase_requisition_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_requisition = PurchaseRequisition.objects.get(pk=1)
        self.assertEqual(purchase_requisition.quantity_requested, 50)

    def test_purchase_requisition_delete_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PurchaseRequisition.objects.count(), 2)

    def test_purchase_requisition_delete_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.delete(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_delete_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_delete_view_status_approved(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.purchase_requisition_delete_status_approved_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_delete_view_status_rejected(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.purchase_requisition_delete_status_rejected_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PurchaseRequisition.objects.count(), 2)

    def test_purchase_requisition_delete_view_unauthenticated(self):
        response = self.client.delete(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(PurchaseRequisition.objects.count(), 3)

    def test_purchase_requisition_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_purchase_requisition_vendor_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_requisition_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        #* Vendor should be able to see only 1 since only pending requisitions are shown
        self.assertEqual(len(response.data), 1)

    def test_purchase_requisition_vendor_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_requisition_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_purchase_requisition_vendor_list_view_unauthenticated(self):
        response = self.client.get(self.purchase_requisition_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_vendor_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.purchase_requisition_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_requisition_vendor_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.purchase_requisition_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SupplierBidViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

        self.purchase_requisition4 = PurchaseRequisition.objects.create(
            requisition_number="PR-004",
            quantity_requested=200,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="high",
            status="pending",
            inventory=self.inventory_item4,
        )

        self.purchase_requisition5 = PurchaseRequisition.objects.create(
            requisition_number="PR-005",
            quantity_requested=250,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="low",
            status="pending",
            inventory=self.inventory_item5,
        )

        self.supplier_bid = SupplierBid.objects.create(
            quantity_fulfilled=50,
            unit_price=10.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition4,
        )

        self.supplier_bid2 = SupplierBid.objects.create(
            quantity_fulfilled=100,
            unit_price=15.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor2,
            requisition=self.purchase_requisition4,
        )

        self.supplier_bid3 = SupplierBid.objects.create(
            quantity_fulfilled=150,
            unit_price=20.00,
            days_delivery=7,
            status="accepted",
            supplier=self.vendor,
            requisition=self.purchase_requisition5,
        )

        self.supplier_bid4 = SupplierBid.objects.create(
            quantity_fulfilled=200,
            unit_price=25.00,
            days_delivery=7,
            status="rejected",
            supplier=self.vendor2,
            requisition=self.purchase_requisition5,
        )

    def test_supplier_bid_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.supplier_bid_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_bid_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_supplier_bid_list_view_unauthenticated(self):
        response = self.client.get(self.supplier_bid_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.supplier_bid_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.supplier_bid_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity_fulfilled"], 50)
        supplier_bid = SupplierBid.objects.get(pk=5)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_create_view_insufficient_quantity_fulfilled(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 5,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_requisition_status_approved(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_requisition_status_approved_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_requisition_status_rejected(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_requisition_status_rejected_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_requisition_bidded(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(reverse("supplier_bid_create", kwargs={'requisition_id': 4}), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_unauthenticated(self):
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "quantity_fulfilled": 50,
            "unit_price": 10.00,
            "days_delivery": 7,
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_missing_data(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.supplier_bid_create_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": "invalid",
            "unit_price": "invalid",
            "days_delivery": "invalid",
        }
        response = self.client.post(self.supplier_bid_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_retrieve_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity_fulfilled"], 50)

    def test_supplier_bid_retrieve_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.get(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_supplier_bid_retrieve_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_bid_retrieve_view_unauthenticated(self):
        response = self.client.get(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.supplier_bid_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_update_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 220,
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity_fulfilled"], 220)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_update_view_status_accepted(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": 250,
        }
        response = self.client.patch(self.supplier_bid_update_status_accepted_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=3)
        self.assertEqual(supplier_bid.quantity_fulfilled, 150)

    def test_supplier_bid_update_view_status_rejected(self):
        self.client.force_authenticate(user=self.vendor2)
        data = {
            "quantity_fulfilled": 300,
        }
        response = self.client.patch(self.supplier_bid_update_status_rejected_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        supplier_bid = SupplierBid.objects.get(pk=4)
        self.assertEqual(supplier_bid.quantity_fulfilled, 300)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_update_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        data = {
            "quantity_fulfilled": 60,
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "quantity_fulfilled": 60,
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_unauthenticated(self):
        data = {
            "quantity_fulfilled": 60,
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "quantity_fulfilled": 60,
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_missing_data(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.patch(self.supplier_bid_update_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "quantity_fulfilled": "invalid",
            "unit_price": "invalid",
            "days_delivery": "invalid",
        }
        response = self.client.patch(self.supplier_bid_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.quantity_fulfilled, 50)

    def test_supplier_bid_delete_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SupplierBid.objects.count(), 3)

    def test_supplier_bid_delete_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.delete(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_delete_view_status_accepted(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.supplier_bid_delete_status_accepted_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_delete_view_status_rejected(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.delete(self.supplier_bid_delete_status_rejected_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SupplierBid.objects.count(), 3)

    def test_supplier_bid_delete_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_delete_view_unauthenticated(self):
        response = self.client.delete(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(SupplierBid.objects.count(), 4)

    def test_supplier_bid_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_procurement_officer_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.supplier_bid_procurment_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_supplier_bid_procurement_officer_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_procurment_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_bid_procurement_officer_list_view_unauthenticated(self):
        response = self.client.get(self.supplier_bid_procurment_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.supplier_bid_procurment_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.supplier_bid_procurment_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_procurement_officer_rank_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.20,
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("dataframe", response.data)
        self.assertIn("radar_plot", response.data)
        self.assertIn("parallel_plot", response.data)

    def test_supplier_bid_procurement_officer_rank_view_sum_not_1(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.30,
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supplier_bid_procurement_officer_rank_view_insufficient_bids(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.20,
        }
        response = self.client.post(reverse("supplier_bid_procurement_officer_ranking", kwargs={'requisition_id': 1}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supplier_bid_procurement_officer_rank_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.20,
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_bid_procurement_officer_rank_view_unauthenticated(self):
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.20,
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_rank_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "weight_unit_price": 0.20,
            "weight_total_cost": 0.20,
            "weight_days_delivery": 0.20,
            "weight_supplier_rating": 0.20,
            "weight_total_ratings": 0.20,
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_rank_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.supplier_bid_procurement_officer_ranking_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_procurement_officer_rank_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supplier_bid_procurement_officer_rank_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "weight_unit_price": "invalid",
            "weight_total_cost": "invalid",
            "weight_days_delivery": "invalid",
            "weight_supplier_rating": "invalid",
            "weight_total_ratings": "invalid",
        }
        response = self.client.post(self.supplier_bid_procurement_officer_ranking_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_supplier_bid_procurement_officer_retrieve_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity_fulfilled"], 50)

    def test_supplier_bid_procurement_officer_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_supplier_bid_procurement_officer_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_supplier_bid_procurement_officer_retrieve_view_unauthenticated(self):
        response = self.client.get(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_supplier_bid_procurement_officer_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.supplier_bid_procurement_officer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_supplier_bid_procurement_officer_status_accept(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "accepted")

        # Check that the other bids are rejected
        other_supplier_bid = SupplierBid.objects.get(pk=2)
        self.assertEqual(other_supplier_bid.status, "rejected")

        # Check that the purchase requisition status is approved
        self.purchase_requisition4.refresh_from_db()
        self.assertEqual(self.purchase_requisition4.status, "approved")

        # Check that the purchase order is created based on the accepted bid
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
        self.assertEqual(purchase_order.bid_id, 1)
    
    def test_supplier_bid_procurement_officer_status_reject(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "rejected",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "rejected")
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "rejected")

        # Check that the other bids are not affected
        other_supplier_bid = SupplierBid.objects.get(pk=2)
        self.assertEqual(other_supplier_bid.status, "submitted")

        # Check that the purchase requisition status is not affected
        self.purchase_requisition4.refresh_from_db()
        self.assertEqual(self.purchase_requisition4.status, "pending")

        # Check that the purchase order is not created
        with self.assertRaises(ObjectDoesNotExist):
            PurchaseOrder.objects.get(pk=1)
    
    def test_supplier_bid_prcourement_officer_bid_accept(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "rejected",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_accepted_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=3)
        self.assertEqual(supplier_bid.status, "accepted") 

    def test_supplier_bid_prcourement_officer_bid_reject(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_rejected_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=4)
        self.assertEqual(supplier_bid.status, "rejected")
    
    def test_supplier_bid_procurement_officer_status_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "accepted")
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "accepted")

    def test_supplier_bid_procurement_officer_status_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_procurement_officer_status_unauthenticated(self):
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_procurement_officer_status_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "status": "accepted",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_procurement_officer_status_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(
            self.supplier_bid_procurement_officer_status_url)
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_procurement_officer_status_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")

    def test_supplier_bid_procurement_officer_status_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "invalid",
        }
        response = self.client.patch(
            self.supplier_bid_procurement_officer_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        supplier_bid = SupplierBid.objects.get(pk=1)
        self.assertEqual(supplier_bid.status, "submitted")


class PurchaseOrderViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

        self.supplier_bid = SupplierBid.objects.create(
            quantity_fulfilled=50,
            unit_price=10.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition,
        )

        self.supplier_bid2 = SupplierBid.objects.create(
            quantity_fulfilled=100,
            unit_price=15.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition2,
        )

        self.supplier_bid3 = SupplierBid.objects.create(
            quantity_fulfilled=150,
            unit_price=20.00,
            days_delivery=7,
            status="accepted",
            supplier=self.vendor,
            requisition=self.purchase_requisition3,
        )

        self.purchase_order = PurchaseOrder.objects.create(
            order_number="PO-001",
            status="pending",
            bid=self.supplier_bid,
        )

        self.purchase_order2 = PurchaseOrder.objects.create(
            order_number="PO-002",
            status="shipped",
            bid=self.supplier_bid2,
        )

        self.purchase_order3 = PurchaseOrder.objects.create(
            order_number="PO-003",
            status="delivered",
            bid=self.supplier_bid3,
        )

    def test_purchase_order_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_order_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_purchase_order_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_order_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_purchase_order_list_view_unauthenticated(self):
        response = self.client.get(self.purchase_order_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_purchase_order_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.purchase_order_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_purchase_order_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.purchase_order_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_purchase_order_vendor_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_order_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_purchase_order_vendor_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.purchase_order_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_purchase_order_vendor_list_view_unauthenticated(self):
        response = self.client.get(self.purchase_order_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_purchase_order_vendor_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.purchase_order_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_purchase_order_vendor_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.purchase_order_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_purchase_order_vendor_status_view_pending_to_pending(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "pending",
        }
        response = self.client.patch(self.purchase_order_vendor_status_pending_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_pending_to_shipped(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_pending_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "shipped")
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "shipped")
    
    def test_purchase_order_vendor_status_view_pending_to_delivered(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "delivered",
        }
        response = self.client.patch(self.purchase_order_vendor_status_pending_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_shipped_to_pending(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "pending",
        }
        response = self.client.patch(self.purchase_order_vendor_status_shipped_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=2)
        self.assertEqual(purchase_order.status, "shipped")
    
    def test_purchase_order_vendor_status_view_shipped_to_shipped(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_shipped_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=2)
        self.assertEqual(purchase_order.status, "shipped")
    
    def test_purchase_order_vendor_status_view_shipped_to_delivered(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "delivered",
        }
        response = self.client.patch(self.purchase_order_vendor_status_shipped_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "delivered")
        purchase_order = PurchaseOrder.objects.get(pk=2)
        self.assertEqual(purchase_order.status, "delivered")
    
    def test_purchase_order_vendor_status_view_delivered_to_pending(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "pending",
        }
        response = self.client.patch(self.purchase_order_vendor_status_delivered_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=3)
        self.assertEqual(purchase_order.status, "delivered")
    
    def test_purchase_order_vendor_status_view_delivered_to_shipped(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_delivered_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=3)
        self.assertEqual(purchase_order.status, "delivered")
    
    def test_purchase_order_vendor_status_view_delivered_to_delivered(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "delivered",
        }
        response = self.client.patch(self.purchase_order_vendor_status_delivered_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=3)
        self.assertEqual(purchase_order.status, "delivered")
    
    def test_purchase_order_vendor_status_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "shipped")
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "shipped")
    
    def test_purchase_order_vendor_status_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_unauthenticated(self):
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "status": "shipped",
        }
        response = self.client.patch(self.purchase_order_vendor_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.purchase_order_vendor_status_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_missing_data(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.patch(self.purchase_order_vendor_status_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
    
    def test_purchase_order_vendor_status_view_invalid_data(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "status": "invalid",
        }
        response = self.client.patch(self.purchase_order_vendor_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase_order = PurchaseOrder.objects.get(pk=1)
        self.assertEqual(purchase_order.status, "pending")
