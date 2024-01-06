from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, exceptions
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .serializers import (
    MyTokenObtainPairSerializer,
    ChangePasswordSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    ProfileSerializer,
    VendorSerializer,
)
from .models import User, Vendor
from .permissions import IsProcurementOfficer


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JSON Web Tokens with added permissions.

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        serializer_class (MyTokenObtainPairSerializer): The serializer class for this view.
    """

    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class ChangePasswordView(generics.UpdateAPIView):
    """
    API view to handle changing a user's password.

    Inherits:
        generics.UpdateAPIView

    Attributes:
        queryset (QuerySet): The queryset to retrieve User objects.
        serializer_class (ChangePasswordSerializer): The serializer class for this view.
    """

    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        """
        Get the user object associated with the request.

        Returns:
            User: The user object.
        """
        return self.request.user


class PasswordResetView(generics.CreateAPIView):
    """
    API view to handle password reset requests.

    Inherits:
        generics.CreateAPIView

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        serializer_class (PasswordResetSerializer): The serializer class for this view.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a password reset request.

        Returns:
            Response: The response indicating the success of the password reset request.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.data["email"])

        # Generate password reset token and URL
        token = default_token_generator.make_token(user)
        pk = str(user.pk)
        password_reset_url = reverse(
            "password_reset_confirm", kwargs={"pk": pk, "token": token}
        )

        print(password_reset_url)

        # Send password reset email
        send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password: {password_reset_url}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"success": "Password reset email sent."})


class PasswordResetConfirmView(generics.UpdateAPIView):
    """
    API view to handle password reset confirmation.

    Inherits:
        generics.UpdateAPIView

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        serializer_class (PasswordResetConfirmSerializer): The serializer class for this view.
    """

    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def get_object(self):
        """
        Get the user object associated with the request.

        Returns:
            User: The user object.
        """
        pk = self.kwargs.get("pk")
        token = self.kwargs.get("token")

        user = User.objects.get(id=int(pk))
        if not user:
            raise exceptions.NotFound("User Not available")

        if not default_token_generator.check_token(user, token):
            raise exceptions.NotFound("Invalid token")

        return user

    def update(self, request, *args, **kwargs):
        """
        Update the user's password.

        Returns:
            Response: The response indicating the success of the password reset.
        """
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]
        user.set_password(password)
        user.save()
        return Response({"detail": "Password reset successful"})


class RegisterView(generics.CreateAPIView):
    """
    API view to handle user registration.

    Inherits:
        generics.CreateAPIView

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        queryset (QuerySet): The queryset to retrieve User objects.
        serializer_class (RegisterSerializer): The serializer class for this view.
    """

    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveAPIView):
    """
    API view to retrieve user profile information.

    Inherits:
        generics.RetrieveAPIView

    Attributes:
        queryset (QuerySet): The queryset to retrieve User objects.
        serializer_class (ProfileSerializer): The serializer class for this view.
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        """
        Get the user object associated with the request.

        Returns:
            User: The user object.
        """
        return self.request.user


class UpdateUserProfileView(generics.UpdateAPIView):
    """
    API view to update user profile information.

    Inherits:
        generics.UpdateAPIView

    Attributes:
        queryset (QuerySet): The queryset to retrieve User objects.
        serializer_class (ProfileSerializer): The serializer class for this view.
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer

    def get_object(self):
        """
        Get the user object associated with the request.

        Returns:
            User: The user object.
        """
        return self.request.user

    def update(self, request, *args, **kwargs):
        """
        Update the user's profile information.

        Returns:
            Response: The response indicating the success of the profile update.
        """
        response = super().update(request, *args, **kwargs)
        return response


class DeleteUserProfileView(generics.DestroyAPIView):
    """
    API view to delete a user's profile.

    Inherits:
        generics.DestroyAPIView

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        queryset (QuerySet): The queryset to retrieve User objects.
    """

    permission_classes = [IsAuthenticated | IsAdminUser]
    queryset = User.objects.all()

    def get_object(self):
        """
        Get the user object associated with the request.

        Returns:
            User: The user object.
        """
        return self.request.user


class VendorView(generics.ListAPIView):
    """
    API view to list vendors.

    Inherits:
        generics.ListAPIView

    Attributes:
        permission_classes (list): The list of permission classes for this view.
        queryset (QuerySet): The queryset to retrieve Vendor objects.
        serializer_class (VendorSerializer): The serializer class for this view.
    """

    permission_classes = [IsAuthenticated, IsAdminUser | IsProcurementOfficer]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def getRoutes(request):
    """
    API view to get a list of available routes in the system.

    Returns:
        Response: The response containing the list of available routes.
    """
    routes = [
        "/token",
        "/token/refresh",
        "/token/verify",
        "/change-password",
        "/password-reset",
        "/password-reset-confirm/<int:pk>/<str:token>/",
        "/register",
        "/profile",
        "/profile/update",
        "/profile/delete",
        "/vendor/list",
    ]

    return Response(routes)
