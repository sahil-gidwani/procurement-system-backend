from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, Vendor
from .models import Inventory, HistoricalInventory, OptimizedInventory


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

        self.inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        self.optimized_inventory_item = OptimizedInventory.objects.create(
            demand=100,
            ordering_cost=10,
            holding_cost=5,
            lead_time=5,
            service_level=0.95,
            safety_stock=10,
            reorder_point=20,
            shelf_life=365,
            storage_limit=200,
            eoq=50,
            inventory=self.inventory_item,
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

        self.inventory_list_url = reverse("inventory_list")
        self.inventory_create_url = reverse("inventory_create")
        self.inventory_retrieve_url = reverse("inventory_retrieve", args=[1])
        self.inventory_update_url = reverse("inventory_update", args=[1])
        self.inventory_delete_url = reverse("inventory_delete", args=[1])
        self.historical_inventory_list_url = reverse("historical_inventory_list", args=[1])
        self.optimized_inventory_retrieve_url = reverse("optimized_inventory_retrieve", args=[1])
        self.optimized_inventory_create_url = reverse("optimized_inventory_create", args=[1])
        self.optimized_inventory_update_url = reverse("optimized_inventory_update", args=[1])
        self.optimized_inventory_delete_url = reverse("optimized_inventory_delete", args=[1])


class InventorySignalsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_create_historical_inventory_on_create(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        historical_inventory_item = HistoricalInventory.objects.get(
            inventory=inventory_item
        )
        self.assertEqual(
            historical_inventory_item.stock_quantity, inventory_item.stock_quantity
        )
        self.assertEqual(historical_inventory_item.datetime,
                         inventory_item.date_added)

    def test_create_historical_inventory_on_update_without_demand(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
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
        self.assertEqual(updated_item.stock_quantity, inventory_item.stock_quantity)
        self.assertEqual(updated_item.demand, 0)
    
    def test_create_historical_inventory_on_update_with_demand(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        inventory_item.stock_quantity = 80
        inventory_item.save()

        historical_inventory_items = HistoricalInventory.objects.filter(
            inventory=inventory_item
        )
        self.assertEqual(historical_inventory_items.count(), 2)

        updated_item = historical_inventory_items.latest("datetime")
        self.assertEqual(updated_item.datetime, inventory_item.last_updated)
        self.assertEqual(updated_item.stock_quantity, inventory_item.stock_quantity)
        self.assertEqual(updated_item.demand, 20)

    def test_delete_historical_inventory_on_inventory_delete(self):
        inventory_item = Inventory.objects.create(
            item_name="Test Item",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
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


class InventoryViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_inventory_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_inventory_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_inventory_list_view_unauthenticated(self):
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_inventory_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Test Item Create",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "location": "Test Location",
        }
        response = self.client.post(self.inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["item_name"], "Test Item Create")
        inventory_item = Inventory.objects.get(item_name="Test Item Create")
        self.assertEqual(inventory_item.procurement_officer, self.procurement_officer)

    def test_inventory_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "location": "Test Location",
        }
        response = self.client.post(self.inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_create_view_unauthenticated(self):
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "location": "Test Location",
        }
        response = self.client.post(self.inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": 10.00,
            "stock_quantity": 100,
            "location": "Test Location",
        }
        response = self.client.post(self.inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_create_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_create_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_create_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Test Item",
            "description": "Test Description",
            "unit_price": "invalid",
            "stock_quantity": "invalid",
            "location": "Test Location",
        }
        response = self.client.post(self.inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Inventory.objects.count(), 1)

    def test_inventory_retrieve_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["item_name"], "Test Item")
    
    def test_inventory_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inventory_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_inventory_retrieve_view_unauthenticated(self):
        response = self.client.get(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_inventory_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inventory_update_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["item_name"], "Updated Item")
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Updated Item")
    
    def test_inventory_update_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_unauthenticated(self):
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": 15.00,
            "stock_quantity": 200,
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.patch(self.inventory_update_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "item_name": "Updated Item",
            "description": "Updated Description",
            "unit_price": "invalid",
            "stock_quantity": "invalid",
            "location": "Updated Location",
        }
        response = self.client.patch(self.inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        inventory_item = Inventory.objects.get(pk=1)
        self.assertEqual(inventory_item.item_name, "Test Item")
    
    def test_inventory_delete_view_procurement_officer_own_item(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Inventory.objects.count(), 0)
    
    def test_inventory_delete_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.delete(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_delete_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_delete_view_unauthenticated(self):
        response = self.client.delete(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_inventory_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(Inventory.objects.count(), 1)
    
    def test_historical_inventory_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_historical_inventory_list_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_historical_inventory_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_historical_inventory_list_view_unauthenticated(self):
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_historical_inventory_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_historical_inventory_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class HistoricalInventoryViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

    def test_historical_inventory_list_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_historical_inventory_list_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_historical_inventory_list_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_historical_inventory_list_view_unauthenticated(self):
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_historical_inventory_list_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_historical_inventory_list_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.historical_inventory_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ARIMAForecastViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

        self.inventory_item2 = Inventory.objects.create(
            item_name="Test Item 2",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )
        
        datetime = timezone.datetime(2021, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        # Create 5 years (260 weeks) of weekly historical inventory data for inventory_item2
        for _ in range(1, 261):
            HistoricalInventory.objects.create(
                stock_quantity=100,
                demand=10,
                datetime=datetime,
                inventory=self.inventory_item2,
            )
            datetime += timedelta(days=7)
        
        self.arima_forecast_url = reverse("arima_forecast", args=[1])
        self.arima_forecast_url2 = reverse("arima_forecast", args=[2])
            

    def test_arima_forecast_view_sufficient_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("annual_forecast", response.data)
    
    def test_arima_forecast_view_insufficient_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.arima_forecast_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_arima_forecast_view_upload_csv_sufficient_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "file": open("inventory/tests/test_data_sufficient_data.csv", "rb")
        }
        response = self.client.post(self.arima_forecast_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("annual_forecast", response.data)
    
    def test_arima_forecast_view_upload_csv_insufficient_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "file": open("inventory/tests/test_data_insufficient_data.csv", "rb")
        }
        response = self.client.post(self.arima_forecast_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_arima_forecast_view_invalid_file_type(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "file": open("inventory/tests/test_data_invalid_file_type.txt", "rb")
        }
        response = self.client.post(self.arima_forecast_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_arima_forecast_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "file": "invalid"
        }
        response = self.client.post(self.arima_forecast_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_arima_forecast_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("annual_forecast", response.data)
    
    def test_arima_forecast_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.arima_forecast_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_arima_forecast_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_arima_forecast_view_unauthenticated(self):
        response = self.client.get(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_arima_forecast_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_arima_forecast_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.arima_forecast_url2)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OptimizedInventoryViewsTests(SetupClass, TestCase):
    def setUp(self):
        super().setUp()

        self.inventory_item2 = Inventory.objects.create(
            item_name="Test Item 2",
            description="Test Description",
            unit_price=10.00,
            stock_quantity=100,
            location="Test Location",
            procurement_officer=self.procurement_officer,
        )

        self.optimized_inventory_create_url2 = reverse("optimized_inventory_create", args=[2])
        
    def test_optimized_inventory_classical_eoq(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["inventory"], 2)
        self.assertIn("eoq", response.data)
        self.assertEqual(response.data["safety_stock"], None)
        self.assertEqual(response.data["reorder_point"], None)
    
    def test_optimized_inventory_eoq_with_rop(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["inventory"], 2)
        self.assertIn("eoq", response.data)
        self.assertIn("safety_stock", response.data)
        self.assertIn("reorder_point", response.data)
    
    def test_optimized_inventory_eoq_for_perishable_items(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "shelf_life": 365,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["inventory"], 2)
        self.assertIn("eoq", response.data)
        self.assertEqual(response.data["safety_stock"], None)
        self.assertEqual(response.data["reorder_point"], None)
    
    def test_optimized_inventory_eoq_for_limited_storage(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "shelf_life": 365,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["inventory"], 2)
        self.assertIn("eoq", response.data)
        self.assertEqual(response.data["safety_stock"], None)
        self.assertEqual(response.data["reorder_point"], None)
    
    def test_optimized_inventory_holding_cost_equals_0(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 0,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_retrieve_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["inventory"], 1)
    
    def test_optimized_inventory_retrieve_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.get(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_retrieve_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_retrieve_view_unauthenticated(self):
        response = self.client.get(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_retrieve_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.get(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_retrieve_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.optimized_inventory_retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_optimized_inventory_create_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["inventory"], 2)
    
    def test_optimized_inventory_create_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_create_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_create_view_unauthenticated(self):
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_create_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_optimized_inventory_create_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.optimized_inventory_create_url2)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_optimized_inventory_create_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.optimized_inventory_create_url2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_create_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": "invalid",
            "ordering_cost": "invalid",
            "holding_cost": "invalid",
            "lead_time": "invalid",
            "service_level": "invalid",
            "shelf_life": "invalid",
            "storage_limit": "invalid",
        }
        response = self.client.post(self.optimized_inventory_create_url2, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_create_view_existing_optimized_inventory(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 100,
            "ordering_cost": 10,
            "holding_cost": 5,
            "lead_time": 5,
            "service_level": 0.95,
            "shelf_life": 365,
            "storage_limit": 200,
        }
        response = self.client.post(self.optimized_inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_create_view_read_only_fields(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "safety_stock": 10,
            "reorder_point": 20,
            "eoq": 50,
        }
        response = self.client.post(self.optimized_inventory_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_update_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": 200,
            "ordering_cost": 20,
            "holding_cost": 10,
            "lead_time": 10,
            "service_level": 0.90,
            "shelf_life": 730,
            "storage_limit": 400,
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["demand"], 200)
    
    def test_optimized_inventory_update_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        data = {
            "demand": 200,
            "ordering_cost": 20,
            "holding_cost": 10,
            "lead_time": 10,
            "service_level": 0.90,
            "shelf_life": 730,
            "storage_limit": 400,
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_update_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        data = {
            "demand": 200,
            "ordering_cost": 20,
            "holding_cost": 10,
            "lead_time": 10,
            "service_level": 0.90,
            "shelf_life": 730,
            "storage_limit": 400,
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_optimized_inventory_update_view_unauthenticated(self):
        data = {
            "demand": 200,
            "ordering_cost": 20,
            "holding_cost": 10,
            "lead_time": 10,
            "service_level": 0.90,
            "shelf_life": 730,
            "storage_limit": 400,
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_update_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        data = {
            "demand": 200,
            "ordering_cost": 20,
            "holding_cost": 10,
            "lead_time": 10,
            "service_level": 0.90,
            "shelf_life": 730,
            "storage_limit": 400,
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_update_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.optimized_inventory_update_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_optimized_inventory_update_view_missing_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.patch(self.optimized_inventory_update_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_update_view_invalid_data(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {
            "demand": "invalid",
            "ordering_cost": "invalid",
            "holding_cost": "invalid",
            "lead_time": "invalid",
            "service_level": "invalid",
            "shelf_life": "invalid",
            "storage_limit": "invalid",
        }
        response = self.client.patch(self.optimized_inventory_update_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_optimized_inventory_delete_view_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OptimizedInventory.objects.count(), 0)
    
    def test_optimized_inventory_delete_view_other_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer2)
        response = self.client.delete(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OptimizedInventory.objects.count(), 1)
    
    def test_optimized_inventory_delete_view_vendor(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OptimizedInventory.objects.count(), 1)
    
    def test_optimized_inventory_delete_view_unauthenticated(self):
        response = self.client.delete(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(OptimizedInventory.objects.count(), 1)
    
    def test_optimized_inventory_delete_view_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.delete(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_optimized_inventory_delete_view_invalid_http_method(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.optimized_inventory_delete_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(OptimizedInventory.objects.count(), 1)
