from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    path('token/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    path('change-password/<int:pk>/', views.ChangePasswordView.as_view(),
         name='auth_change_password'),
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    re_path(r'^password-reset-confirm/(?P<pk>\d+)/(?P<token>[^/]+)/$', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('vendor/', views.VendorView.as_view(), name='vendor')
]
