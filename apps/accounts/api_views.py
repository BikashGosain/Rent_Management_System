from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import OTP
from .otp_utils import send_otp
from .serializers import (
    RegisterSerializer,
    OTPVerifySerializer,
    ResendOTPSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)


def get_tokens(user):
    """Return JWT access + refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ── Register ──────────────────────────────────────────────────────────────────


class RegisterAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "detail": "Account created. OTP sent to your email.",
                    "user_id": user.pk,
                    "email": user.email,
                    # Frontend should use user_id + purpose='register' to call /verify-otp/
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── OTP Verify ────────────────────────────────────────────────────────────────


class VerifyOTPAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            otp = serializer.validated_data["otp"]
            purpose = serializer.validated_data["purpose"]

            # Mark OTP used
            otp.is_used = True
            otp.save(update_fields=["is_used"])

            if purpose == "register":
                user.is_active = True
                user.is_verified = True
                user.save(update_fields=["is_active", "is_verified"])
                return Response(
                    {
                        "detail": "Account verified successfully.",
                        "tokens": get_tokens(user),
                        "user": UserProfileSerializer(user).data,
                    },
                    status=status.HTTP_200_OK,
                )

            elif purpose == "forgot_password":
                # Mark reset as allowed — return a short-lived token
                return Response(
                    {
                        "detail": "OTP verified. You can now reset your password.",
                        "user_id": user.pk,
                        # Frontend calls /reset-password/ with this user_id
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Resend OTP ────────────────────────────────────────────────────────────────


class ResendOTPAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            purpose = serializer.validated_data["purpose"]
            otp = OTP.generate(user, purpose)
            send_otp(user, otp)
            return Response(
                {
                    "detail": "OTP resent successfully.",
                    "user_id": user.pk,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Login ─────────────────────────────────────────────────────────────────────


class LoginAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            return Response(
                {
                    "detail": "Login successful.",
                    "tokens": get_tokens(user),
                    "user": UserProfileSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Logout ────────────────────────────────────────────────────────────────────


class LogoutAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh = request.data.get("refresh")
            token = RefreshToken(refresh)
            token.blacklist()  # blacklist the refresh token
            return Response(
                {"detail": "Logged out successfully."}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )


# ── Forgot Password ───────────────────────────────────────────────────────────


class ForgotPasswordAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "detail": "OTP sent to your email.",
                    "user_id": user.pk,
                    # Frontend → call /verify-otp/ with purpose='forgot_password'
                    # Then call /reset-password/ with user_id
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Reset Password ────────────────────────────────────────────────────────────


class ResetPasswordAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password reset successful. Please login."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────────────


class ProfileAPI(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True  # allow partial updates (PATCH)
        return super().update(request, *args, **kwargs)


# ── Change Password ───────────────────────────────────────────────────────────


class ChangePasswordAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
