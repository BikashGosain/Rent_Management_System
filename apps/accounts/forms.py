from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class RegisterForm(forms.ModelForm):
    REGISTER_ROLE_CHOICES = [
        ("owner", "🏠 House Owner"),
        ("tenant", "🔑 Tenant"),
    ]

    role = forms.ChoiceField(
        choices=REGISTER_ROLE_CHOICES,
        widget=forms.Select(),
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
        label="Password",
        min_length=8,
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone", "role"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First Name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last Name"}),
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email Address"}),
            "phone": forms.TextInput(attrs={"placeholder": "+977-98XXXXXXXX"}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Delete old unverified account with same username
        User.objects.filter(
            username=username, is_active=False, is_verified=False
        ).delete()
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Delete old unverified account with same email
        User.objects.filter(email=email, is_active=False, is_verified=False).delete()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered with an active account."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        user.is_verified = False
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"placeholder": "Username or Email"}
        )
        self.fields["password"].widget.attrs.update({"placeholder": "Password"})


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                "placeholder": "000000",
                "maxlength": "6",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "class": "otp-input",
            }
        ),
        label="Enter 6-digit OTP",
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Enter your registered email"}),
        label="Email Address",
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email, is_active=True).exists():
            raise forms.ValidationError("No active account found with this email.")
        return email


class ResetPasswordForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "New Password"}),
        min_length=8,
        label="New Password",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm New Password"}),
        label="Confirm Password",
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "photo",
            "address",
            "bio",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "bio": forms.Textarea(attrs={"rows": 3}),
        }
