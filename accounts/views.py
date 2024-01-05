from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, exceptions
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from .serializer import MyTokenObtainPairSerializer, ChangePasswordSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, RegisterSerializer, ProfileSerializer, VendorSerializer
from .models import User, Vendor
from .permissions import IsProcurementOfficer


class MyTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MyTokenObtainPairSerializer


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer
    
    def get_object(self):
        return self.request.user
    

class PasswordResetView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.data['email'])

        # Generate password reset token and URL
        token = default_token_generator.make_token(user)
        pk = str(user.pk)
        password_reset_url = reverse('password_reset_confirm', kwargs={
                                     'pk': pk, 'token': token})

        print(password_reset_url)

        # Send password reset email
        send_mail(
            subject='Password Reset Request',
            message=f'Click the link to reset your password: {password_reset_url}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"success": "Password reset email sent."})


class PasswordResetConfirmView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def get_object(self):
        pk = self.kwargs.get('pk')
        token = self.kwargs.get('token')

        user = User.objects.get(id=int(pk))
        if not user:
            raise exceptions.NotFound('User Not available')

        if not default_token_generator.check_token(user, token):
            raise exceptions.NotFound("Invalid token")

        return user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()
        return Response({'detail': 'Password reset successful'})


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


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
        return response

class DeleteUserProfileView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser]
    queryset = User.objects.all()

    def get_object(self):
        return self.request.user


class VendorView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminUser | IsProcurementOfficer]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def getRoutes(request):
    routes = [
        '/token',
        '/token/refresh',
        '/token/verify',
        '/change-password',
        '/password-reset',
        '/password-reset-confirm/<int:pk>/<str:token>/',
        '/register',
        '/profile',
        '/profile/update',
        '/profile/delete',
        '/vendor/list',
    ]

    return Response(routes)
