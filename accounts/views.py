from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, exceptions
from rest_framework.permissions import AllowAny
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from .serializer import MyTokenObtainPairSerializer, RegisterSerializer, ChangePasswordSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, VendorSerializer
from .models import User, Vendor


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ChangePasswordView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer


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
            from_email='settings.EMAIL_HOST_USER',
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"success": "Password reset email sent."})


class PasswordResetConfirmView(generics.UpdateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def get_object(self, *args, **kwargs):
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


class VendorView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
