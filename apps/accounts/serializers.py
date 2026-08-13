from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, OTP
from .otp_utils import send_otp


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    ROLE_CHOICES = [('owner', 'House Owner'), ('tenant', 'Tenant')]

    role      = serializers.ChoiceField(choices=ROLE_CHOICES)
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role', 'password1', 'password2']

    def validate_email(self, value):
        # Delete old unverified accounts with same email (mirrors your form logic)
        User.objects.filter(email=value, is_active=False, is_verified=False).delete()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value

    def validate_username(self, value):
        User.objects.filter(username=value, is_active=False, is_verified=False).delete()
        return value

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = User(**validated_data)
        user.set_password(password)
        user.is_active   = False
        user.is_verified = False
        user.save()
        # Generate + send OTP (same as your register_view)
        otp = OTP.generate(user, 'register')
        send_otp(user, otp)
        return user


# ── OTP ───────────────────────────────────────────────────────────────────────

class OTPVerifySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    purpose = serializers.ChoiceField(choices=['register', 'forgot_password', 'login'])
    code    = serializers.CharField(min_length=6, max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})

        otp = OTP.objects.filter(
            user=user, purpose=data['purpose'], is_used=False
        ).order_by('-created_at').first()

        if not otp:
            raise serializers.ValidationError({'code': 'No active OTP found. Please resend.'})
        if otp.is_expired():
            raise serializers.ValidationError({'code': 'OTP expired. Please resend.'})
        if otp.attempts >= 3:
            raise serializers.ValidationError({'code': 'Too many attempts. Please resend OTP.'})

        otp.attempts += 1
        otp.save(update_fields=['attempts'])

        if otp.code != data['code']:
            remaining = 3 - otp.attempts
            raise serializers.ValidationError({'code': f'Wrong OTP. {remaining} attempt(s) left.'})

        data['user'] = user
        data['otp']  = otp
        return data


class ResendOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    purpose = serializers.ChoiceField(choices=['register', 'forgot_password', 'login'])

    def validate(self, data):
        try:
            user = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})

        last_otp = OTP.objects.filter(
            user=user, purpose=data['purpose']
        ).order_by('-created_at').first()

        if last_otp and not last_otp.can_resend():
            wait = last_otp.seconds_until_resend()
            raise serializers.ValidationError({'detail': f'Wait {wait} seconds before resending.'})

        data['user'] = user
        return data


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid username or password.'})
        if not user.is_active:
            # Not verified — return user_id so frontend can redirect to OTP
            raise serializers.ValidationError({
                'detail':  'Account not verified.',
                'user_id': user.pk,
                'action':  'verify_otp',
            })
        data['user'] = user
        return data


# ── Forgot / Reset Password ───────────────────────────────────────────────────

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError('No active account with this email.')
        self.user = user
        return value

    def save(self):
        otp = OTP.generate(self.user, 'forgot_password')
        send_otp(self.user, otp)
        return self.user


class ResetPasswordSerializer(serializers.Serializer):
    user_id   = serializers.IntegerField()
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        try:
            data['user'] = User.objects.get(pk=data['user_id'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password1'])
        user.save()
        return user


# ── Profile ───────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'phone', 'role', 'photo',
            'address', 'bio', 'is_verified', 'date_joined',
        ]
        read_only_fields = ['id', 'username', 'role', 'is_verified', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(write_only=True)
    new_password1 = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Passwords do not match.'})
        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        return user