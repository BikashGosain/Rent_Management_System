from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # Auth
    path("register/", api_views.RegisterAPI.as_view(), name="api-register"),
    path("verify-otp/", api_views.VerifyOTPAPI.as_view(), name="api-verify-otp"),
    path("resend-otp/", api_views.ResendOTPAPI.as_view(), name="api-resend-otp"),
    path("login/", api_views.LoginAPI.as_view(), name="api-login"),
    path("logout/", api_views.LogoutAPI.as_view(), name="api-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    # Password
    path(
        "forgot-password/",
        api_views.ForgotPasswordAPI.as_view(),
        name="api-forgot-password",
    ),
    path(
        "reset-password/",
        api_views.ResetPasswordAPI.as_view(),
        name="api-reset-password",
    ),
    # Profile
    path("profile/", api_views.ProfileAPI.as_view(), name="api-profile"),
    path(
        "change-password/",
        api_views.ChangePasswordAPI.as_view(),
        name="api-change-password",
    ),
]
