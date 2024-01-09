from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User, Vendor
from .models import Inventory, HistoricalInventory


class InventoryModelsTestCase(TestCase):
    def setUp(self):
        self.procurement_officer = User.objects.create_user(
            username="procurement_officer",
            email="procurement_officer@example.com",
            password="testpassword",
            user_role="procurement_officer",
        )

    def test_create_historical_inventory_on_create(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            reorder_level=20,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        historical_inventory_item = HistoricalInventory.objects.get(
            inventory=inventory_item
        )
        self.assertEqual(
            historical_inventory_item.stock_quantity, inventory_item.stock_quantity
        )
        self.assertEqual(historical_inventory_item.datetime, inventory_item.date_added)

    def test_create_historical_inventory_on_update(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            reorder_level=20,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        inventory_item.stock_quantity = 150
        inventory_item.save()

        historical_inventory_items = HistoricalInventory.objects.filter(
            inventory=inventory_item
        )
        self.assertEqual(historical_inventory_items.count(), 2)

        updated_item = historical_inventory_items.latest("datetime")
        self.assertEqual(updated_item.datetime, inventory_item.last_updated)

    def test_delete_historical_inventory_on_inventory_delete(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            reorder_level=20,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        inventory_item.save()

        historical_inventory_items = HistoricalInventory.objects.filter(
            inventory=inventory_item
        )
        self.assertTrue(historical_inventory_items.exists())

        inventory_item.delete()

        with self.assertRaises(ObjectDoesNotExist):
            inventory_item.refresh_from_db()
            historical_inventory_items_after_delete = (
                HistoricalInventory.objects.filter(inventory=inventory_item)
            )
            self.assertFalse(historical_inventory_items_after_delete.exists())


class InventoryViewsTestCase(TestCase):
    def setUp(self):
        self.procurement_officer = User.objects.create_user(
            username="procurement_officer",
            email="procurement_officer@example.com",
            password="testpassword",
            user_role="procurement_officer",
        )
        self.vendor = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="testpassword",
            user_role="vendor",
        )
        Vendor.objects.create(
            user=self.vendor,
            vendor_name="Vendor Corporation",
            address="123 Main St",
            vendor_certified=True,
            vendor_type="Supplier",
            contract_expiry_date="2023-12-31",
            vendor_rating=4.5,
        )

        self.client = APIClient()

    def test_inventory_list_view_procurement_officer(self):
        url = reverse("inventory_list")
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inventory_list_view_vendor(self):
        url = reverse("inventory_list")
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_create_view_procurement_officer(self):
        url = reverse("inventory_create")
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "reorder_level": 20,
            "location": "Test Location",
            "procurement_officer": self.procurement_officer.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_inventory_create_view_vendor(self):
        url = reverse("inventory_create")
        self.client.force_authenticate(user=self.vendor)
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "reorder_level": 20,
            "location": "Test Location",
            "procurement_officer": self.procurement_officer.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def create_inventory_item(self):
        return Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            reorder_level=20,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

    def test_inventory_retrieve_view_procurement_officer(self):
        inventory_item = self.create_inventory_item()
        url = reverse("inventory_retrieve", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inventory_retrieve_view_vendor(self):
        inventory_item = self.create_inventory_item()
        url = reverse("inventory_retrieve", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inventory_update_view_procurement_officer_own_item(self):
        inventory_item = self.create_inventory_item()
        url = reverse("inventory_update", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "reorder_level": 30,
            "location": "Updated Location",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inventory_item.refresh_from_db()
        self.assertEqual(inventory_item.item_name, "Updated Item")

    def test_inventory_update_view_procurement_officer_other_item(self):
        other_procurement_officer = User.objects.create_user(
            username="other_procurement_officer",
            email="other_procurement_officer@example.com",
            password="testpassword",
            user_role="procurement_officer",
        )
        inventory_item = self.create_inventory_item()
        inventory_item.procurement_officer = other_procurement_officer
        inventory_item.save()

        url = reverse("inventory_update", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "reorder_level": 30,
            "location": "Updated Location",
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_delete_view_procurement_officer_own_item(self):
        inventory_item = self.create_inventory_item()
        url = reverse("inventory_delete", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Inventory.objects.filter(pk=inventory_item.pk).exists())

    def test_inventory_delete_view_procurement_officer_other_item(self):
        other_procurement_officer = User.objects.create_user(
            username="other_procurement_officer",
            email="other_procurement_officer@example.com",
            password="testpassword",
            user_role="procurement_officer",
        )
        inventory_item = self.create_inventory_item()
        inventory_item.procurement_officer = other_procurement_officer
        inventory_item.save()

        url = reverse("inventory_delete", kwargs={"pk": inventory_item.pk})
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Inventory.objects.filter(pk=inventory_item.pk).exists())

    def test_historical_inventory_list_view_procurement_officer(self):
        # Create an inventory item for the procurement officer
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            reorder_level=20,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        url = reverse(
            "historical_inventory_list", kwargs={"inventory_id": inventory_item.id}
        )
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_historical_inventory_list_view_procurement_officer_invalid_inventory_id(
        self,
    ):
        url = reverse("historical_inventory_list", kwargs={"inventory_id": 999})
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
