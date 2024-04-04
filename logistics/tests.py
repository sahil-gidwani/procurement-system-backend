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
from purchase.models import PurchaseRequisition, SupplierBid, PurchaseOrder
from .models import InventoryReceipt, Invoice


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

        self.purchase_requisition4 = PurchaseRequisition.objects.create(
            requisition_number="PR-004",
            quantity_requested=200,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="medium",
            status="pending",
            inventory=self.inventory_item4,
        )

        self.purchase_requisition5 = PurchaseRequisition.objects.create(
            requisition_number="PR-005",
            quantity_requested=250,
            expected_delivery_date=(timezone.now() + timedelta(days=7)).date(),
            urgency_level="high",
            status="approved",
            inventory=self.inventory_item5,
        )

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
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition3,
        )

        self.supplier_bid4 = SupplierBid.objects.create(
            quantity_fulfilled=200,
            unit_price=25.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition4,
        )

        self.supplier_bid5 = SupplierBid.objects.create(
            quantity_fulfilled=250,
            unit_price=30.00,
            days_delivery=7,
            status="submitted",
            supplier=self.vendor,
            requisition=self.purchase_requisition5,
        )

        self.purchase_order = PurchaseOrder.objects.create(
            order_number="PO-001",
            status="delivered",
            bid=self.supplier_bid,
        )

        self.purchase_order2 = PurchaseOrder.objects.create(
            order_number="PO-002",
            status="pending",
            bid=self.supplier_bid2,
        )

        self.purchase_order3 = PurchaseOrder.objects.create(
            order_number="PO-003",
            status="shipped",
            bid=self.supplier_bid3,
        )

        self.purchase_order4 = PurchaseOrder.objects.create(
            order_number="PO-004",
            status="delivered",
            bid=self.supplier_bid4,
        )

        self.purchase_order5 = PurchaseOrder.objects.create(
            order_number="PO-005",
            status="delivered",
            bid=self.supplier_bid5,
        )

        self.inventory_receipt = InventoryReceipt.objects.create(
            receipt_id="IR-001",
            received_quantity=50,
            received_condition="good",
            inspection_notes="Test Notes",
            order=self.purchase_order,
        )

        self.inventory_receipt2 = InventoryReceipt.objects.create(
            receipt_id="IR-002",
            received_quantity=100,
            received_condition="good",
            inspection_notes="Test Notes",
            order=self.purchase_order2,
        )

        self.inventory_receipt3 = InventoryReceipt.objects.create(
            receipt_id="IR-003",
            received_quantity=150,
            received_condition="good",
            inspection_notes="Test Notes",
            order=self.purchase_order3,
        )

        self.invoice = Invoice.objects.create(
            invoice_number="INV-001",
            account_number="1234567890",
            total_amount=500.00,
            payment_due_date=(timezone.now() + timedelta(days=30)).date(),
            payment_mode="credit",
            order=self.purchase_order,
        )

        self.invoice2 = Invoice.objects.create(
            invoice_number="INV-002",
            account_number="1234567891",
            total_amount=1500.00,
            payment_due_date=(timezone.now() + timedelta(days=30)).date(),
            payment_mode="debit",
            payment_status="paid",
            vendor_rated=False,
            order=self.purchase_order2,
        )

        self.invoice3 = Invoice.objects.create(
            invoice_number="INV-003",
            account_number="1234567892",
            total_amount=2500.00,
            payment_due_date=(timezone.now() + timedelta(days=30)).date(),
            payment_mode="cash",
            payment_status="pending",
            vendor_rated=True,
            order=self.purchase_order3,
        )

        self.inventory_receipt_list_url = reverse("inventory_receipt_list")
        self.inventory_receipt_create_duplicate_url = reverse(
            "inventory_receipt_create", kwargs={"order_id": 1}
        )
        self.inventory_receipt_create_order_status_pending_url = reverse(
            "inventory_receipt_create", kwargs={"order_id": 2}
        )
        self.inventory_receipt_create_order_status_shipped_url = reverse(
            "inventory_receipt_create", kwargs={"order_id": 3}
        )
        self.inventory_receipt_create_order_status_delivered_url = reverse(
            "inventory_receipt_create", kwargs={"order_id": 4}
        )
        self.inventory_receipt_create_url = reverse(
            "inventory_receipt_create", kwargs={"order_id": 5}
        )
        self.inventory_receipt_retrieve_url = reverse(
            "inventory_receipt_detail", kwargs={"pk": 1}
        )
        self.inventory_receipt_update_url = reverse(
            "inventory_receipt_update", kwargs={"pk": 1}
        )
        self.inventory_receipt_delete_url = reverse(
            "inventory_receipt_delete", kwargs={"pk": 1}
        )
        self.inventory_receipt_vendor_list_url = reverse(
            "inventory_receipt_vendor_list"
        )
        self.inventory_receipt_vendor_retrieve_url = reverse(
            "inventory_receipt_vendor_detail", kwargs={"pk": 1}
        )
        self.invoice_list_url = reverse("invoice_list")
        self.invoice_create_duplicate_url = reverse(
            "invoice_create", kwargs={"order_id": 1}
        )
        self.invoice_create_order_status_pending_url = reverse(
            "invoice_create", kwargs={"order_id": 2}
        )
        self.invoice_create_order_status_shipped_url = reverse(
            "invoice_create", kwargs={"order_id": 3}
        )
        self.invoice_create_order_status_delivered_url = reverse(
            "invoice_create", kwargs={"order_id": 4}
        )
        self.invoice_create_url = reverse("invoice_create", kwargs={"order_id": 5})
        self.invoice_retrieve_url = reverse("invoice_detail", kwargs={"pk": 1})
        self.invoice_update_url = reverse("invoice_update", kwargs={"pk": 1})
        self.invoice_delete_url = reverse("invoice_delete", kwargs={"pk": 1})
        self.invoice_procurement_officer_list_url = reverse(
            "invoice_procurement_officer_list"
        )
        self.invoice_procurement_officer_retrieve_url = reverse(
            "invoice_procurement_officer_detail", kwargs={"pk": 1}
        )
        self.invoice_payment_status_url = reverse(
            "invoice_payment_status", kwargs={"pk": 1}
        )
        self.invoice_payment_status_paid_url = reverse(
            "invoice_payment_status", kwargs={"pk": 2}
        )
        self.invoice_vendor_rating_url = reverse(
            "invoice_vendor_rating", kwargs={"pk": 2}
        )
        self.invoice_vendor_rating_rated_url = reverse(
            "invoice_vendor_rating", kwargs={"pk": 3}
        )
        self.invoice_vendor_rating_unpaid_url = reverse(
            "invoice_vendor_rating", kwargs={"pk": 1}
        )


class InventoryReceiptTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_inventory_receipt_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_inventory_receipt_list_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_inventory_receipt_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_list_view_unauthenticated(self):
        response = self.client.get(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_receipt_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_receipt_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-004",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["receipt_id"], "IR-004")
        inventory_receipt = InventoryReceipt.objects.get(receipt_id="IR-004")
        self.assertEqual(inventory_receipt.order.order_number, "PO-005")

    def test_inventory_receipt_create_view_one_to_one_purchase_order(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_duplicate_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_order_status_pending(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(
            self.inventory_receipt_create_order_status_pending_url, data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_order_status_shipped(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-003",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(
            self.inventory_receipt_create_order_status_shipped_url, data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_order_status_delivered(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-004",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(
            self.inventory_receipt_create_order_status_delivered_url, data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["receipt_id"], "IR-004")
        inventory_receipt = InventoryReceipt.objects.get(receipt_id="IR-004")
        self.assertEqual(inventory_receipt.order.order_number, "PO-004")

    def test_inventory_receipt_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_unauthenticated(self):
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "receipt_id": "IR-002",
            "received_quantity": 50,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_receipt_create_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-002",
            "received_quantity": "invalid",
            "received_condition": "invalid",
            "inspection_notes": "invalid",
        }
        response = self.client.post(self.inventory_receipt_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(InventoryReceipt.objects.count(), 3)

    def test_inventory_receipt_retrieve_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["receipt_id"], "IR-001")

    def test_inventory_receipt_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_receipt_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_retrieve_view_unauthenticated(self):
        response = self.client.get(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_receipt_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_receipt_update_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "receipt_id": "IR-001",
            "received_quantity": 60,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inventory_receipt = InventoryReceipt.objects.get(receipt_id="IR-001")
        self.assertEqual(inventory_receipt.received_quantity, 60)

    def test_inventory_receipt_update_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "received_quantity": 60,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_receipt_update_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "received_quantity": 60,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_update_view_unauthenticated(self):
        data = {
            "received_quantity": 60,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "received_quantity": 60,
            "received_condition": "good",
            "inspection_notes": "Test Notes",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_receipt_update_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.put(self.inventory_receipt_update_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inventory_receipt_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "received_quantity": "invalid",
            "received_condition": "invalid",
            "inspection_notes": "invalid",
        }
        response = self.client.put(self.inventory_receipt_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inventory_receipt_delete_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(ObjectDoesNotExist):
            InventoryReceipt.objects.get(receipt_id="IR-001")

    def test_inventory_receipt_delete_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.delete(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_receipt_delete_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_delete_view_unauthenticated(self):
        response = self.client.delete(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_receipt_vendor_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_inventory_receipt_vendor_list_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.get(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_inventory_receipt_vendor_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_vendor_list_view_unauthenticated(self):
        response = self.client.get(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_vendor_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_vendor_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.inventory_receipt_vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_receipt_vendor_retrieve_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["receipt_id"], "IR-001")

    def test_inventory_receipt_vendor_retrieve_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.get(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_receipt_vendor_retrieve_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_receipt_vendor_retrieve_view_unauthenticated(self):
        response = self.client.get(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_vendor_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inventory_receipt_vendor_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.inventory_receipt_vendor_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class InvoiceTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_invoice_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_invoice_list_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.get(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_invoice_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_list_view_unauthenticated(self):
        response = self.client.get(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.invoice_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-004",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice_number"], "INV-004")
        invoice = Invoice.objects.get(invoice_number="INV-004")
        self.assertEqual(invoice.order.order_number, "PO-005")

    def test_invoice_create_view_one_to_one_purchase_order(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_duplicate_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_order_status_pending(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_order_status_pending_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_order_status_shipped(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-003",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_order_status_shipped_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_order_status_delivered(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-004",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(
            self.invoice_create_order_status_delivered_url, data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoice_number"], "INV-004")
        invoice = Invoice.objects.get(invoice_number="INV-004")
        self.assertEqual(invoice.order.order_number, "PO-004")

    def test_invoice_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_unauthenticated(self):
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "invoice_number": "INV-002",
            "account_number": "1234567890",
            "total_amount": 500.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_missing_data(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.invoice_create_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-002",
            "account_number": "invalid",
            "total_amount": "invalid",
            "payment_due_date": "invalid",
            "payment_mode": "invalid",
        }
        response = self.client.post(self.invoice_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Invoice.objects.count(), 3)

    def test_invoice_retrieve_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoice_number"], "INV-001")

    def test_invoice_retrieve_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.get(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_retrieve_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_retrieve_view_unauthenticated(self):
        response = self.client.get(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.post(self.invoice_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_update_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "invoice_number": "INV-001",
            "account_number": "1234567891",
            "total_amount": 600.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice = Invoice.objects.get(invoice_number="INV-001")
        self.assertEqual(invoice.total_amount, 600.00)

    def test_invoice_update_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        data = {
            "account_number": "1234567891",
            "total_amount": 600.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_update_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "account_number": "1234567891",
            "total_amount": 600.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_update_view_unauthenticated(self):
        data = {
            "account_number": "1234567891",
            "total_amount": 600.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "account_number": "1234567891",
            "total_amount": 600.00,
            "payment_due_date": (timezone.now() + timedelta(days=30)).date(),
            "payment_mode": "credit",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_update_view_missing_data(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.put(self.invoice_update_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "account_number": "invalid",
            "total_amount": "invalid",
            "payment_due_date": "invalid",
            "payment_mode": "invalid",
        }
        response = self.client.put(self.invoice_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_delete_view_vendor_own_item(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(ObjectDoesNotExist):
            Invoice.objects.get(invoice_number="INV-001")

    def test_invoice_delete_view_other_vendor(self):
        self.client.force_authenticate(user=self.vendor2)
        response = self.client.delete(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_delete_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_delete_view_unauthenticated(self):
        response = self.client.delete(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_procurement_officer_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_invoice_procurement_officer_list_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_invoice_procurement_officer_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_procurement_officer_list_view_unauthenticated(self):
        response = self.client.get(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_procurement_officer_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_procurement_officer_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.invoice_procurement_officer_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_procurement_officer_retrieve_view_procurement_officer_own_item(
        self,
    ):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoice_number"], "INV-001")

    def test_invoice_procurement_officer_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_procurement_officer_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_procurement_officer_retrieve_view_unauthenticated(self):
        response = self.client.get(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_procurement_officer_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_procurement_officer_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.invoice_procurement_officer_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_payment_status_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice = Invoice.objects.get(invoice_number="INV-001")
        self.assertEqual(invoice.payment_status, "paid")

    def test_invoice_payment_status_view_status_paid(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_paid_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_payment_status_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_payment_status_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_payment_status_view_unauthenticated(self):
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_payment_status_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {"payment_status": "paid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_payment_status_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_payment_status_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_payment_status_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.patch(self.invoice_payment_status_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_payment_status_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"payment_status": "invalid"}
        response = self.client.put(self.invoice_payment_status_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_vendor_rating_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice = Invoice.objects.get(invoice_number="INV-002")
        self.assertEqual(invoice.vendor_rated, True)

    def test_invoice_vendor_rating_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invoice_vendor_rating_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invoice_vendor_rating_view_unauthenticated(self):
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_vendor_rating_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invoice_vendor_rating_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.invoice_vendor_rating_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invoice_vendor_rating_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.put(self.invoice_vendor_rating_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_vendor_rating_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"vendor_rating": "invalid"}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_vendor_rating_view_vendor_rated(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_rated_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_vendor_rating_view_unpaid(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"vendor_rating": 5}
        response = self.client.put(self.invoice_vendor_rating_unpaid_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invoice_vendpr_rating_view_invalid_rating(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"vendor_rating": 6}
        response = self.client.put(self.invoice_vendor_rating_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
