from datetime import timedelta
from django.urls import reverse
from django.core import mail
from django.core.cache import cache
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase
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


class SetUpUsers(APITestCase):
    def setUp(self):
        cache.clear()

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

        self.token_obtain_url = reverse("token_obtain_pair")
        self.token_refresh_url = reverse("token_refresh")
        # self.token_verify_url = reverse("token_verify")
        self.change_password_url = reverse("change_password")
        self.password_reset_url = reverse("password_reset")
        self.password_reset_confirm_url = reverse(
            "password_reset_confirm",
            kwargs={"pk": self.procurement_officer.pk, "token": "token"},
        )
        self.procurement_officer_register_url = reverse("procurement_officer_register")
        self.vendor_register_url = reverse("vendor_register")
        self.user_profile_url = reverse("user_profile")
        self.update_profile_url = reverse("update_user_profile")
        self.delete_profile_url = reverse("delete_user_profile")
        self.vendor_list_url = reverse("vendor_list")


class TokenViewTests(SetUpUsers, APITestCase):
    def setUp(self):
        super().setUp()

    def test_obtain_token(self):
        data = {
            "username": "procurement_officer",
            "password": "testpassword",
        }
        response = self.client.post(self.token_obtain_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_with_invalid_credentials(self):
        data = {
            "username": "procurement_officer",
            "password": "invalidpassword",
        }
        response = self.client.post(self.token_obtain_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtain_token_with_missing_credentials(self):
        data = {
            "username": "procurement_officer",
        }
        response = self.client.post(self.token_obtain_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_token(self):
        refresh = RefreshToken.for_user(self.procurement_officer)
        data = {
            "refresh": str(refresh),
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_token_with_invalid_token(self):
        data = {
            "refresh": "invalidtoken",
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_with_expired_token(self):
        refresh = RefreshToken.for_user(self.procurement_officer)
        refresh.set_exp(lifetime=timedelta(seconds=-1))
        data = {
            "refresh": str(refresh),
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_with_blacklisted_token(self):
        token = RefreshToken.for_user(self.procurement_officer)
        token.blacklist()
        data = {
            "refresh": str(token.access_token),
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_which_was_used_previously(self):
        refresh = RefreshToken.for_user(self.procurement_officer)
        data = {
            "refresh": str(refresh),
        }
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.token_refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # * The following tests are for the TokenVerifyView, which is not used in the project

    # def test_verify_token(self):
    #     token = RefreshToken.for_user(self.procurement_officer)
    #     data = {
    #         "token": str(token.access_token),
    #     }
    #     response = self.client.post(self.token_verify_url, data, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_verify_token_with_invalid_token(self):
    #     data = {
    #         "token": "invalidtoken",
    #     }
    #     response = self.client.post(self.token_verify_url, data, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_verify_token_with_expired_token(self):
    #     token = RefreshToken.for_user(self.procurement_officer)
    #     token.set_exp(lifetime=timedelta(seconds=-1))
    #     data = {
    #         "token": str(token.access_token),
    #     }
    #     response = self.client.post(self.token_verify_url, data, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # def test_verify_token_with_blacklisted_token(self):
    #     token = RefreshToken.for_user(self.procurement_officer)
    #     token.blacklist()
    #     data = {
    #         "token": str(token.access_token),
    #     }
    #     response = self.client.post(self.token_verify_url, data, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordViewTests(SetUpUsers, APITestCase):
    def setUp(self):
        super().setUp()

    def test_change_password_successfully(self):
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

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
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        new_password_data = {
            "old_password": "invalidpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_mismatched_passwords(self):
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
            "password2": "mismatchedpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_providing_old_password(self):
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        new_password_data = {
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_invalid_http_authorization_header(self):
        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_invalid_http_method(self):
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
            "password2": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_change_password_with_invalid_payload(self):
        login_data = {"username": "procurement_officer", "password": "testpassword"}
        login_response = self.client.post(
            self.token_obtain_url, login_data, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        token = login_response.data["access"]

        new_password_data = {
            "old_password": "testpassword",
            "password1": "newtestpassword",
        }
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.put(
            self.change_password_url, new_password_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetViewTests(SetUpUsers, APITestCase):
    def setUp(self):
        super().setUp()

    #! Mails unable to send in test environment with Celery

    def test_password_reset_successful(self):
        data = {"email": "procurement_officer@example.com"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(mail.outbox), 1)
        self.assertIn("success", response.data)

    def test_password_reset_with_invalid_email(self):
        data = {"email": "invalidemail"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_missing_email(self):
        data = {}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_unregistered_email(self):
        data = {"email": "unregistered@example.com"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_invalid_http_method(self):
        data = {"email": "procurement_officer@example.com"}
        response = self.client.get(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_invalid_payload(self):
        data = {"invalidkey": "1234"}
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_with_authenticated_user(self):
        data = {"email": "procurement_officer@example.com"}
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.post(self.password_reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(len(mail.outbox), 1)


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

    def test_password_reset_confirm_with_mismatched_passwords(self):
        data = {"password": "newtestpassword", "confirm_password": "mismatchedpassword"}
        response = self.client.put(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_with_invalid_token(self):
        invalid_token_url = reverse(
            "password_reset_confirm",
            kwargs={"pk": self.user.pk, "token": "invalidtoken"},
        )
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        response = self.client.put(invalid_token_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset_confirm_with_invalid_user(self):
        invalid_user_url = reverse(
            "password_reset_confirm",
            kwargs={"pk": 1234, "token": default_token_generator.make_token(self.user)},
        )
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        response = self.client.put(invalid_user_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset_confirm_with_invalid_http_method(self):
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        response = self.client.get(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_password_reset_confirm_with_invalid_payload(self):
        data = {"invalidkey": "1234"}
        response = self.client.put(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_with_authenticated_user(self):
        data = {"password": "newtestpassword", "confirm_password": "newtestpassword"}
        self.client.force_authenticate(user=self.user)
        response = self.client.put(self.password_reset_confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProcurementOfficerRegisterViewTests(APITestCase):
    def setUp(self):
        self.procurement_officer_register_url = reverse("procurement_officer_register")

    def test_register_procurement_officer_user(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "12ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
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

    def test_register_user_with_password_mismatch(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "52ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
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
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
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
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_invalid_gstin(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "invalidgstin",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_existing_username(self):
        User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email="johndoe@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="procurement_officer",
        )
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe2@example.com",
            "phone_number": "1234567891",
            "gstin": "82ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_user_with_existing_email(self):
        User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email="johndoe@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="procurement_officer",
        )
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe2",
            "email": "johndoe@example.com",
            "phone_number": "1234567891",
            "gstin": "82ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_user_with_existing_gstin(self):
        User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="johndoe",
            email="johndoe@example.com",
            phone_number="1234567890",
            gstin="12ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="procurement_officer",
        )
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe2",
            "email": "johndoe2@example.com",
            "phone_number": "1234567891",
            "gstin": "12ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_user_with_invalid_http_method(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "12ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        response = self.client.get(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_invalid_payload(self):
        data = {"invalidkey": "1234"}
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_user_with_authenticated_user(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "johndoe@example.com",
            "phone_number": "1234567890",
            "gstin": "12ABCDE1234F1Z5",
            "company_name": "Procurement Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
        }
        user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            username="authenticateduser",
            email="authenticateduser@example.com",
            phone_number="1234567890",
            gstin="22ABCDE1234F1Z5",
            company_name="Procurement Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="procurement_officer",
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(
            self.procurement_officer_register_url, data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)


class VendorRegisterViewTests(APITestCase):
    def setUp(self):
        self.vendor_register_url = reverse("vendor_register")

    def test_register_vendor_user(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Vendor.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, "janesmith")
        self.assertEqual(user.email, "janesmith@example.com")
        self.assertEqual(user.phone_number, "9876543210")
        self.assertEqual(user.user_role, "vendor")
        self.assertTrue(hasattr(user, "vendor"))
        vendor = user.vendor
        self.assertTrue(vendor.vendor_certified)
        self.assertEqual(vendor.vendor_type, "supplier")

    def test_register_user_with_password_mismatch(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "passwordmismatch",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_invalid_email(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "invalidemail",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_invalid_phone_number(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "invalidphonenumber",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_invalid_gstin(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "invalidgstin",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_existing_username(self):
        User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="janesmith",
            email="janesmith@example.com",
            phone_number="9876543210",
            gstin="42ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="vendor",
        )
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith2@example.com",
            "phone_number": "9876543210",
            "gstin": "52ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_existing_email(self):
        User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="janesmith",
            email="janesmith@example.com",
            phone_number="9876543210",
            gstin="42ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="vendor",
        )
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith2",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "52ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_existing_gstin(self):
        User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="janesmith",
            email="janesmith@example.com",
            phone_number="9876543210",
            gstin="42ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="vendor",
        )
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith2",
            "email": "janesmith2@example.com",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_invalid_http_method(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "invalidphonenumber",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        response = self.client.get(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_invalid_payload(self):
        data = {"invalidkey": "1234"}
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Vendor.objects.count(), 0)

    def test_register_user_with_authenticated_user(self):
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "username": "janesmith",
            "email": "janesmith@example.com",
            "phone_number": "9876543210",
            "gstin": "42ABCDE1234F1Z5",
            "company_name": "Vendor Corporation",
            "address": "123 Main St",
            "password1": "yourpassword",
            "password2": "yourpassword",
            "vendor_info": {
                "vendor_certified": True,
                "vendor_type": "supplier",
            },
        }
        user = User.objects.create_user(
            first_name="Jane",
            last_name="Smith",
            username="authenticateduser",
            email="authenticateduser@example.com",
            phone_number="9876543210",
            gstin="52ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="yourpassword",
            user_role="vendor",
        )
        self.client.force_authenticate(user=user)
        response = self.client.post(self.vendor_register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(Vendor.objects.count(), 1)


class UserProfileViewTests(SetUpUsers):
    def setUp(self):
        super().setUp()

    def test_get_procurement_officer_profile(self):
        self.client.force_authenticate(user=self.procurement_officer)
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "procurement_officer")

    def test_get_vendor_profile(self):
        self.client.force_authenticate(user=self.vendor)
        response = self.client.get(self.user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "vendor")

    def test_get_user_profile_unauthenticated(self):
        response = self.client.get(self.user_profile_url)
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
        cache.clear()

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
            company_name="Procurement Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="procurement_officer",
        )
        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            gstin="52ABCDE1234F1Z5",
            company_name="Vendor Corporation",
            address="123 Main St",
            password="testpassword",
            user_role="vendor",
        )

        self.vendor_list_url = reverse("vendor_list")

    def test_no_vendors(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_vendor_list(self):
        Vendor.objects.create(
            user=self.vendor_user, vendor_certified=True, vendor_type="supplier"
        )
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.vendor_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

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
