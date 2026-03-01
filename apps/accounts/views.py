from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import User, OTP
from .forms import (
    RegisterForm, LoginForm, OTPVerifyForm,
    ForgotPasswordForm, ResetPasswordForm, ProfileUpdateForm,
)
from .otp_utils import send_otp


# ── Register ──────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # is_active=False
            otp  = OTP.generate(user, 'register')
            ok   = send_otp(user, otp)

            # Store user pk in session for OTP step
            request.session['otp_user_id'] = user.pk
            request.session['otp_purpose']  = 'register'

            if ok:
                messages.success(request, f'OTP sent to {user.email} and {user.phone or "your phone"}.')
            else:
                messages.warning(request, 'Account created but OTP delivery failed. Use resend.')

            return redirect('accounts:verify_otp')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# ── OTP Verify ────────────────────────────────────────────────────────────────

def verify_otp_view(request):
    user_id = request.session.get('otp_user_id')
    purpose = request.session.get('otp_purpose')

    if not user_id or not purpose:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('accounts:register')

    user = get_object_or_404(User, pk=user_id)
    otp  = OTP.objects.filter(
        user=user, purpose=purpose, is_used=False
    ).order_by('-created_at').first()

    resend_wait = otp.seconds_until_resend() if otp else 0

    if request.method == 'POST':
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']

            if not otp or otp.is_expired():
                messages.error(request, 'OTP expired. Please resend.')
                return redirect('accounts:verify_otp')

            if otp.attempts >= 3:
                messages.error(request, 'Too many attempts. Please resend OTP.')
                return redirect('accounts:verify_otp')

            otp.attempts += 1
            otp.save(update_fields=['attempts'])

            if otp.code != code:
                remaining = 3 - otp.attempts
                messages.error(request, f'Wrong OTP. {remaining} attempt(s) remaining.')
                return render(request, 'accounts/verify_otp.html', {
                    'form': form, 'purpose': purpose,
                    'email': user.email, 'phone': user.phone,
                    'resend_wait': resend_wait,
                })

            # ── OTP correct ──
            otp.is_used = True
            otp.save(update_fields=['is_used'])

            if purpose == 'register':
                user.is_active   = True
                user.is_verified = True
                user.save(update_fields=['is_active', 'is_verified'])
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                # Clear session
                del request.session['otp_user_id']
                del request.session['otp_purpose']
                messages.success(request, f'Welcome to RentMS, {user.first_name or user.username}! 🎉')
                return redirect('core:home')

            elif purpose == 'forgot_password':
                # Allow password reset — store flag in session
                request.session['reset_verified'] = True
                messages.success(request, 'OTP verified! Now set your new password.')
                return redirect('accounts:reset_password')
    else:
        form = OTPVerifyForm()

    return render(request, 'accounts/verify_otp.html', {
        'form':        form,
        'purpose':     purpose,
        'email':       user.email,
        'phone':       user.phone,
        'resend_wait': resend_wait,
        'masked_email': mask_email(user.email),
        'masked_phone': mask_phone(user.phone),
    })


def resend_otp_view(request):
    user_id = request.session.get('otp_user_id')
    purpose = request.session.get('otp_purpose')

    if not user_id or not purpose:
        messages.error(request, 'Session expired.')
        return redirect('accounts:register')

    user = get_object_or_404(User, pk=user_id)

    # Check last OTP resend wait
    last_otp = OTP.objects.filter(user=user, purpose=purpose).order_by('-created_at').first()
    if last_otp and not last_otp.can_resend():
        wait = last_otp.seconds_until_resend()
        messages.warning(request, f'Please wait {wait} seconds before resending.')
        return redirect('accounts:verify_otp')

    otp = OTP.generate(user, purpose)
    ok  = send_otp(user, otp)

    if ok:
        messages.success(request, f'New OTP sent to {mask_email(user.email)} and {mask_phone(user.phone)}.')
    else:
        messages.error(request, 'Failed to send OTP. Please try again.')

    return redirect('accounts:verify_otp')


# ── Login ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                request.session['otp_user_id'] = user.pk
                request.session['otp_purpose']  = 'register'
                otp = OTP.generate(user, 'register')
                send_otp(user, otp)
                messages.warning(request, 'Account not verified. OTP sent.')
                return redirect('accounts:verify_otp')

            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})



def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


# ── Forgot Password ───────────────────────────────────────────────────────────

def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user  = User.objects.get(email=email)

            otp = OTP.generate(user, 'forgot_password')
            send_otp(user, otp)

            request.session['otp_user_id'] = user.pk
            request.session['otp_purpose']  = 'forgot_password'

            messages.success(request, f'OTP sent to {mask_email(email)}.')
            return redirect('accounts:verify_otp')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


def reset_password_view(request):
    if not request.session.get('reset_verified'):
        messages.error(request, 'Please verify OTP first.')
        return redirect('accounts:forgot_password')

    user_id = request.session.get('otp_user_id')
    user    = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.save()
            # Clear session
            for key in ['otp_user_id', 'otp_purpose', 'reset_verified']:
                request.session.pop(key, None)
            messages.success(request, 'Password reset successful! Please login.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form, 'user': user})


# ── Social Auth Complete ───────────────────────────────────────────────────────

def social_complete_view(request):
    """After Google OAuth — ask for role if not set. Skip for superusers/admins."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    user = request.user

    # Superusers and existing admins go straight home
    if user.is_superuser or user.role == 'admin':
        return redirect('core:home')

    # If role already properly set, go home
    if user.role in ['owner', 'tenant']:
        return redirect('core:home')

    # New Google user — needs to pick role
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['owner', 'tenant']:
            user.role = role
            user.save(update_fields=['role'])
            messages.success(request, f'Welcome to RentMS, {user.first_name or user.username}! 🎉')
            return redirect('core:home')
        else:
            messages.error(request, 'Please select a role to continue.')

    return render(request, 'accounts/social_role.html', {'user': user})


# ── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/password_change.html', {'form': form})


# ── Helpers ───────────────────────────────────────────────────────────────────


def redirect_by_role(user):
    """Send each role to their correct dashboard."""
    if user.is_superuser or user.role == 'admin':
        return redirect('dashboard:admin')
    elif user.role == 'owner':
        return redirect('dashboard:owner')
    elif user.role == 'tenant':
        return redirect('dashboard:tenant')
    return redirect('core:home')


def mask_email(email):
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f'{"*" * len(local)}@{domain}'
    return f'{local[:2]}{"*" * (len(local)-2)}@{domain}'


def mask_phone(phone):
    if not phone or len(phone) < 4:
        return phone or ''
    return f'{"*" * (len(phone)-4)}{phone[-4:]}'

