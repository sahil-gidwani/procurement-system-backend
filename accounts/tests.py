from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Vendor


# class ThrottleTestCase(TestCase):
#     def setUp(self):
#         self.test_user = User.objects.create_user(username='testuser', password='testpassword')
#         self.client = APIClient()

#     def test_anonymous_throttle(self):
#         for _ in range(100):
#             response = self.client.get(reverse('accounts_routes'))
#             self.assertEqual(response.status_code, 200)

#         response = self.client.get(reverse('accounts_routes'))
#         self.assertEqual(response.status_code, 429)

#     def test_authenticated_user_throttle(self):
#         self.client.force_authenticate(user=self.test_user)

#         for _ in range(1000):
#             response = self.client.get(reverse('accounts_routes'))
#             self.assertEqual(response.status_code, 200)

#         response = self.client.get(reverse('accounts_routes'))
#         self.assertEqual(response.status_code, 429)


class TokenViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
        )
        self.token_obtain_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")
        self.token_verify_url = reverse("token_verify")

    def test_obtain_token(self):
        data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(self.token_obtain_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        data = {
            "refresh": str(refresh),
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_verify_token(self):
        token = RefreshToken.for_user(self.user)
        data = {
            "token": str(token.access_token),
        }
        response = self.client.post(self.token_verify_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChangePasswordViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
        )
        self.change_password_url = reverse("change_password")
        self.login_url = reverse("token_obtain_pair")

    def test_change_password_successfully(self):
        login_data = {"username": "testuser", "password": "testpassword"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        # Change password
        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_invalid_old_password(self):
        login_data = {"username": "testuser", "password": "testpassword"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        # Attempt to change password with invalid old password
        new_password_data = {
            "old_password": "wrongpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("old_password", response.data)


class PasswordResetViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
        )
        self.password_reset_url = reverse("password_reset")

    def test_password_reset_email_sent(self):
        data = {"email": "testuser@example.com"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success"], "Password reset email sent.")

        # Check that the email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Password Reset Request")

    def test_password_reset_with_invalid_email(self):
        data = {"email": "invalid@example.com"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["email"][0], "User with this email ID doesn't exist."
        )


class PasswordResetConfirmViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
        )
        self.password_reset_confirm_url = reverse(
            "password_reset_confirm",
            kwargs={
                "pk": self.user.pk,
                "token": default_token_generator.make_token(self.user),
            },
        )

    def test_password_reset_confirm_successful(self):
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        response = self.client.put(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Password reset successful")

    def test_password_reset_confirm_with_mismatched_passwords(self):
        data = {"password": "newtestpassword", "confirm_password": "mismatchedpassword"}
        response = self.client.put(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_password_reset_confirm_with_invalid_token(self):
        invalid_token_url = reverse(
            "password_reset_confirm",
            kwargs={"pk": self.user.pk, "token": "invalidtoken"},
        )
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        response = self.client.put(invalid_token_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.procurement_officer_register_url = reverse("procurement_officer_register")
        self.vendor_register_url = reverse("vendor_register")

    def test_register_procurement_officer_user(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "12ABCDE1234F1Z5",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, "johndoe")
        self.assertEqual(user.email, "johndoe@example.com")
        self.assertEqual(user.phone_number, "1234567890")
        self.assertEqual(user.user_role, "procurement_officer")
        self.assertFalse(hasattr(user, "vendor"))

    def test_register_vendor_user(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_name": "ABC Corporation",
                "address": "123 Main St, Cityville",
                "vendor_certified": True,
                "vendor_type": "supplier",
                "contract_expiry_date": "2023-12-31",
                "vendor_rating": 4.5,
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, "janesmith")
        self.assertEqual(user.email, "janesmith@example.com")
        self.assertEqual(user.phone_number, "9876543210")
        self.assertEqual(user.user_role, "vendor")
        self.assertTrue(hasattr(user, "vendor"))
        vendor = user.vendor
        self.assertEqual(vendor.vendor_name, "ABC Corporation")
        self.assertEqual(vendor.address, "123 Main St, Cityville")
        self.assertTrue(vendor.vendor_certified)
        self.assertEqual(vendor.vendor_type, "supplier")
        self.assertEqual(str(vendor.contract_expiry_date), "2023-12-31")
        self.assertEqual(vendor.vendor_rating, 4.5)

    def test_register_user_with_password_mismatch(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "52ABCDE1234F1Z5",
            "password1": "yourpassword",
            "password2": "mismatchedpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_invalid_email(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "invalidemail",
            "phone_number": "1234567890",
            "gstin": "62ABCDE1234F1Z5",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_invalid_phone_number(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "invalidphonenumber",
            "gstin": "72ABCDE1234F1Z5",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class SetUpUsers(APITestCase):
    def setUp(self):
        self.procurement_officer = User.objects.create_user(
            username="procurement_officer",
            email="procurement_officer@example.com",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
            user_role="procurement_officer",
        )
        self.vendor = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            gstin="42ABCDE1234F1Z5",
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


class UserProfileViewTests(SetUpUsers):
    def setUp(self):
        super().setUp()
        self.profile_url = reverse("user_profile")
        self.update_profile_url = reverse("update_user_profile")
        self.delete_profile_url = reverse("delete_user_profile")

    def test_get_procurement_officer_profile(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_vendor_profile(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_procurement_officer_profile(self):
        self.client.force_authenticate(user=self.procurement_officer)
        data = {"username": "new_procurement_username"}
        response = self.client.patch(self.update_profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.procurement_officer.refresh_from_db()
        self.assertEqual(self.procurement_officer.username, "new_procurement_username")

    def test_update_vendor_profile(self):
        self.client.force_authenticate(user=self.vendor)
        data = {"username": "new_vendor_username"}
        response = self.client.patch(self.update_profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.username, "new_vendor_username")

    def test_update_user_profile_unauthenticated(self):
        data = {"username": "new_username"}
        response = self.client.patch(self.update_profile_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_procurement_officer_profile(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.delete(self.delete_profile_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertRaises(
            User.DoesNotExist, User.objects.get, username="procurement_officer"
        )

    def test_delete_vendor_profile(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.delete(self.delete_profile_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertRaises(User.DoesNotExist, User.objects.get, username="vendor")

    def test_delete_user_profile_unauthenticated(self):
        response = self.client.delete(self.delete_profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VendorListViewTests(APITestCase):
    def setUp(self):
        self.vendor_list_url = reverse("vendor_list")
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            gstin="12ABCDE1234F1Z5",
            password="testpassword",
            is_staff=True,
            is_superuser=True,
        )
        self.procurement_officer_user = User.objects.create_user(
            username="procurement_officer",
            email="procurement_officer@example.com",
            gstin="42ABCDE1234F1Z5",
            password="testpassword",
            user_role="procurement_officer",
        )
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            gstin="52ABCDE1234F1Z5",
            password="testpassword",
            user_role="vendor",
        )

    def test_no_vendors(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_list(self):
        Vendor.objects.create(
            user=self.vendor_user,
            vendor_name="Test Vendor",
            address="123 Test Street, Test City, Test Country",
            vendor_certified=True,
            vendor_type="supplier",
            contract_expiry_date=date.today(),
            vendor_rating=4.5,
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sufficient_permissions_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sufficient_permissions_procurement_officer(self):
        self.client.force_authenticate(user=self.procurement_officer_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_insufficient_permissions_vendor(self):
        self.client.force_authenticate(user=self.vendor_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
