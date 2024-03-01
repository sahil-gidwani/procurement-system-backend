from rest_framework import generics, exceptions, serializers
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from drf_spectacular.utils import extend_schema
from .serializers import (
    MyTokenObtainPairSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ProcurementOfficerRegisterSerializer,
    VendorRegisterSerializer,
    ProfileSerializer,
    VendorSerializer,
)
from .models import User, Vendor
from .permissions import IsProcurementOfficer
from .tasks import (
    send_password_change_email,
    send_password_reset_email,
    send_password_reset_confirm_email,
    send_register_email,
    send_update_profile_email,
)


class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        # Send password change email confirmation asynchronously
        send_password_change_email.delay(request.user.email)

        return response


class PasswordResetView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.data["email"])

        # Generate password reset token and URL
        token = default_token_generator.make_token(user)
        pk = str(user.pk)
        password_reset_url = reverse(
            "password_reset_confirm", kwargs={"pk": pk, "token": token}
        )

        password_reset_url = settings.FRONTEND_URL + password_reset_url

        # Send password reset email asynchronously
        send_password_reset_email.delay(user.email, password_reset_url)

        return Response({"success": "Password reset email sent."})


class PasswordResetConfirmView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def get_object(self):
        pk = self.kwargs.get("pk")
        token = self.kwargs.get("token")

        user = User.objects.get(id=int(pk))
        if not user:
            raise exceptions.NotFound("User Not available")

        if not default_token_generator.check_token(user, token):
            raise exceptions.NotFound("Invalid token")

        return user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()

        # Send password reset email confirmation asynchronously
        send_password_reset_confirm_email.delay(user.email)

        return Response({"detail": "Password reset successful"})


class ProcurementOfficerRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = ProcurementOfficerRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        send_register_email.delay(user.email)


class VendorRegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = VendorRegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        send_register_email.delay(user.email)
        cache_key = "vendor_list"
        cache.delete(cache_key)


class UserProfileView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


class UpdateUserProfileView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        # Send updated profile email confirmation asynchronously
        send_update_profile_email.delay(request.user.email)

        return response


class DeleteUserProfileView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser]
    serializer_class = serializers.ModelSerializer
    queryset = User.objects.all()
    model = User
    fields = "__all__"

    def get_object(self):
        return self.request.user


class VendorView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser | IsProcurementOfficer]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def list(self, request, *args, **kwargs):
        cache_key = "vendor_list"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60 * 60 * 24 * 7)
        return response


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        "/token",
        "/token/refresh",
        "/token/verify",
        "/change-password",
        "/password-reset",
        "/password-reset-confirm/<int:pk>/<str:token>/",
        "/register/procurement-officer",
        "/register/vendor",
        "/profile",
        "/profile/update",
        "/profile/delete",
        "/vendor/list",
    ]

    return Response(routes)
