from django.core.mail import send_mail
from django.conf import settings
from .models import Notification


def send_notification(recipient, notif_type, title, message, link='', send_email=True):
    """Create in-app notification and optionally send email."""

    # Create in-app notification
    notification = Notification.objects.create(
        recipient  = recipient,
        notif_type = notif_type,
        title      = title,
        message    = message,
        link       = link,
    )

    # Send email
    if send_email and recipient.email:
        try:
            send_mail(
                subject      = f'RentMS — {title}',
                message      = f'{message}\n\nLogin to view details: {settings.SITE_URL if hasattr(settings, "SITE_URL") else "http://127.0.0.1:8000"}{link}',
                from_email   = settings.DEFAULT_FROM_EMAIL,
                recipient_list = [recipient.email],
                fail_silently  = True,
            )
        except Exception:
            pass

    return notification


# ── Notification Helpers ──────────────────────────────────────────────────────

def notify_booking_received(booking):
    owner = booking.get_owner()
    send_notification(
        recipient  = owner,
        notif_type = 'booking_received',
        title      = 'New Booking Request',
        message    = f'{booking.tenant.get_full_name() or booking.tenant.username} has requested to book {booking.get_target_name()}.',
        link       = f'/bookings/{booking.pk}/',
    )


def notify_booking_accepted(booking):
    send_notification(
        recipient  = booking.tenant,
        notif_type = 'booking_accepted',
        title      = 'Booking Accepted! 🎉',
        message    = f'Your booking for {booking.get_target_name()} has been accepted by the owner.',
        link       = f'/bookings/{booking.pk}/',
    )


def notify_booking_rejected(booking):
    send_notification(
        recipient  = booking.tenant,
        notif_type = 'booking_rejected',
        title      = 'Booking Rejected',
        message    = f'Your booking for {booking.get_target_name()} has been rejected.',
        link       = f'/bookings/{booking.pk}/',
    )


def notify_agreement_created(agreement):
    send_notification(
        recipient  = agreement.tenant,
        notif_type = 'agreement_created',
        title      = 'Agreement Created — Please Sign',
        message    = f'A rental agreement for {agreement.get_target_name()} has been created. Please review and sign.',
        link       = f'/agreements/{agreement.pk}/',
    )


def notify_agreement_signed(agreement, signed_by):
    # Notify the other party
    if signed_by == agreement.owner:
        recipient = agreement.tenant
        message   = f'The owner has signed the agreement for {agreement.get_target_name()}. Please sign to activate.'
    else:
        recipient = agreement.owner
        message   = f'The tenant has signed the agreement for {agreement.get_target_name()}.'

    send_notification(
        recipient  = recipient,
        notif_type = 'agreement_signed',
        title      = 'Agreement Signed',
        message    = message,
        link       = f'/agreements/{agreement.pk}/',
    )

    # If both signed, notify both
    if agreement.owner_signed and agreement.tenant_signed:
        send_notification(
            recipient  = agreement.owner,
            notif_type = 'agreement_signed',
            title      = 'Agreement is Now Active! ✅',
            message    = f'Both parties have signed. Agreement for {agreement.get_target_name()} is now active.',
            link       = f'/agreements/{agreement.pk}/',
        )
        send_notification(
            recipient  = agreement.tenant,
            notif_type = 'agreement_signed',
            title      = 'Agreement is Now Active! ✅',
            message    = f'Both parties have signed. Agreement for {agreement.get_target_name()} is now active.',
            link       = f'/agreements/{agreement.pk}/',
        )


def notify_agreement_terminated(agreement, terminated_by):
    # Notify the other party
    if terminated_by == agreement.owner:
        recipient = agreement.tenant
        message   = f'The owner has terminated the agreement for {agreement.get_target_name()}.'
    else:
        recipient = agreement.owner
        message   = f'The tenant has terminated the agreement for {agreement.get_target_name()}.'

    send_notification(
        recipient  = recipient,
        notif_type = 'agreement_terminated',
        title      = 'Agreement Terminated',
        message    = message,
        link       = f'/agreements/{agreement.pk}/',
    )


def notify_payment_received(payment):
    send_notification(
        recipient  = payment.tenant,
        notif_type = 'payment_received',
        title      = 'Payment Marked as Received',
        message    = f'Your {payment.get_payment_type_display()} of Rs. {payment.amount} has been confirmed by the owner.',
        link       = f'/payments/{payment.pk}/',
    )


def notify_payment_due(payment):
    send_notification(
        recipient  = payment.tenant,
        notif_type = 'payment_due',
        title      = f'Payment Due — {payment.get_month_display_name()}',
        message    = f'Your {payment.get_payment_type_display()} of Rs. {payment.amount} is due on {payment.due_date}.',
        link       = f'/payments/{payment.pk}/',
    )


def notify_complaint_submitted(complaint):
    if complaint.submitted_by == 'owner':
        # Owner raised issue — notify tenant
        send_notification(
            recipient  = complaint.tenant,
            notif_type = 'complaint_submitted',
            title      = '⚠️ Issue Raised Against You',
            message    = f'Your owner has raised an issue: {complaint.title}. Please review and respond.',
            link       = f'/complaints/{complaint.pk}/',
        )
    else:
        # Tenant submitted complaint — notify owner
        send_notification(
            recipient  = complaint.owner,
            notif_type = 'complaint_submitted',
            title      = 'New Complaint Received',
            message    = f'{complaint.tenant.get_full_name() or complaint.tenant.username} submitted a complaint: {complaint.title}',
            link       = f'/complaints/{complaint.pk}/',
        )

def notify_complaint_response(complaint, responder):
    # Notify the other party
    if responder == complaint.owner:
        recipient = complaint.tenant
        message   = f'The owner responded to your complaint: {complaint.title}'
    else:
        recipient = complaint.owner
        message   = f'The tenant responded to complaint: {complaint.title}'

    send_notification(
        recipient  = recipient,
        notif_type = 'complaint_response',
        title      = 'Complaint Response Received',
        message    = message,
        link       = f'/complaints/{complaint.pk}/',
    )