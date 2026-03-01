from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',         views.register_view,        name='register'),
    path('login/',            views.login_view,            name='login'),
    path('logout/',           views.logout_view,           name='logout'),
    path('verify-otp/',       views.verify_otp_view,       name='verify_otp'),
    path('resend-otp/',       views.resend_otp_view,       name='resend_otp'),
    path('forgot-password/',  views.forgot_password_view,  name='forgot_password'),
    path('reset-password/',   views.reset_password_view,   name='reset_password'),
    path('social/complete/',  views.social_complete_view,  name='social_complete'),
    path('profile/',          views.profile_view,          name='profile'),
    path('profile/edit/',     views.edit_profile_view,     name='edit_profile'),   # ← new
    path('password-change/',  views.password_change_view,  name='password_change'),
]