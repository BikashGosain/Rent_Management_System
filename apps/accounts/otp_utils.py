from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_otp_email(user, otp):
    """Send OTP to user email."""
    subject = f'Your RentMS Verification Code: {otp.code}'
    message = f"""
Hi {user.first_name or user.username},

Your verification code is:

    {otp.code}

This code expires in 5 minutes.
Do not share this code with anyone.

— RentMS Team
"""
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        otp.sent_email = True
        otp.save(update_fields=['sent_email'])
        return True
    except Exception as e:
        print(f'Email OTP error: {e}')
        return False


def send_otp_sms(user, otp):
    """Send OTP via Twilio SMS."""
    if not user.phone:
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f'Your RentMS verification code is: {otp.code}. Valid for 5 minutes. Do not share.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=user.phone,
        )
        otp.sent_sms = True
        otp.save(update_fields=['sent_sms'])
        return True
    except Exception as e:
        print(f'SMS OTP error: {e}')
        return False


def send_otp(user, otp):
    """Send OTP via both email and SMS."""
    email_ok = send_otp_email(user, otp)
    sms_ok   = send_otp_sms(user, otp)
    return email_ok or sms_ok  # success if at least one works