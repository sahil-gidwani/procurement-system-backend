from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

urlpatterns = [
    path("", views.getRoutes, name="accounts_routes"),
    path("token/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),
    path("password-reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/<int:pk>/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "register/procurement-officer/",
        views.ProcurementOfficerRegisterView.as_view(),
        name="procurement_officer_register",
    ),
    path(
        "register/vendor/", views.VendorRegisterView.as_view(), name="vendor_register"
    ),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    path(
        "profile/update/",
        views.UpdateUserProfileView.as_view(),
        name="update_user_profile",
    ),
    path(
        "profile/delete/",
        views.DeleteUserProfileView.as_view(),
        name="delete_user_profile",
    ),
    path("vendor/list/", views.VendorView.as_view(), name="vendor_list"),
]
