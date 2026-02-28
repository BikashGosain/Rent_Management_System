from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.db.models import Sum, Count, Avg


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not (request.user.is_admin() or request.user.is_superuser):
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_owner():
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_tenant():
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def admin_dashboard(request):
    from apps.accounts.models import User
    from apps.properties.models import Property
    from apps.bookings.models import Booking
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint
    from apps.agreements.models import Agreement

    context = {
        'total_users':       User.objects.count(),
        'total_owners':      User.objects.filter(role='owner').count(),
        'total_tenants':     User.objects.filter(role='tenant').count(),
        'total_properties':  Property.objects.count(),
        'total_bookings':    Booking.objects.count(),
        'total_payments':    Payment.objects.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,
        'total_complaints':  Complaint.objects.filter(status='open').count(),
        'total_agreements':  Agreement.objects.filter(status='active').count(),
        'recent_users':      User.objects.order_by('-date_joined')[:5],
        'recent_bookings':   Booking.objects.order_by('-created_at')[:5],
        'open_complaints':   Complaint.objects.filter(status='open').order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/admin.html', context)


@owner_required
def owner_dashboard(request):
    from apps.properties.models import Property
    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    # Properties
    whole_properties = Property.objects.filter(owner=request.user, rent_type='whole')
    room_properties  = Property.objects.filter(owner=request.user, rent_type='rooms')
    all_properties   = Property.objects.filter(owner=request.user)

    # Bookings
    pending_bookings = Booking.objects.filter(
        property__owner=request.user, status='pending'
    ) | Booking.objects.filter(
        room__property__owner=request.user, status='pending'
    )
    recent_bookings = Booking.objects.filter(
        property__owner=request.user
    ) | Booking.objects.filter(
        room__property__owner=request.user
    )
    recent_bookings = recent_bookings.order_by('-created_at')[:5]

    # Agreements
    active_agreements = Agreement.objects.filter(owner=request.user, status='active')

    # Payments
    recent_payments  = Payment.objects.filter(owner=request.user, status='paid').order_by('-paid_date')[:5]
    total_received   = Payment.objects.filter(owner=request.user, status='paid').aggregate(t=Sum('amount'))['t'] or 0
    pending_payments = Payment.objects.filter(owner=request.user, status__in=['pending', 'overdue']).count()

    # Complaints
    open_complaints = Complaint.objects.filter(
        owner=request.user, status__in=['open', 'in_progress']
    ).order_by('-created_at')[:5]

    # Activity feed (mix of recent actions)
    activity = []
    for b in Booking.objects.filter(
        property__owner=request.user
    ).order_by('-created_at')[:3]:
        activity.append({
            'icon': '🏠', 'text': f'New booking request for {b.get_target_name()}',
            'time': b.created_at, 'link': f'/bookings/{b.pk}/'
        })
    for p in Payment.objects.filter(
        owner=request.user, status='paid'
    ).order_by('-paid_date')[:3]:
        activity.append({
            'icon': '💰', 'text': f'Payment received: Rs. {p.amount}',
            'time': p.updated_at, 'link': f'/payments/{p.pk}/'
        })
    for c in Complaint.objects.filter(
        owner=request.user
    ).order_by('-created_at')[:3]:
        activity.append({
            'icon': '⚠️', 'text': f'Complaint: {c.title}',
            'time': c.created_at, 'link': f'/complaints/{c.pk}/'
        })
    activity = sorted(activity, key=lambda x: x['time'], reverse=True)[:8]

    context = {
        # Properties
        'whole_properties':   whole_properties,
        'room_properties':    room_properties,
        'all_properties':     all_properties,
        'total_whole':        whole_properties.count(),
        'total_room_props':   room_properties.count(),
        'available_props':    all_properties.filter(status='available').count(),
        'occupied_props':     all_properties.filter(status='occupied').count(),

        # Bookings
        'pending_bookings':   pending_bookings.order_by('-created_at')[:5],
        'pending_count':      pending_bookings.count(),
        'recent_bookings':    recent_bookings,

        # Agreements
        'active_agreements':  active_agreements,
        'active_tenants':     active_agreements.count(),

        # Payments
        'recent_payments':    recent_payments,
        'total_received':     total_received,
        'pending_payments':   pending_payments,

        # Complaints
        'open_complaints':    open_complaints,
        'open_count':         open_complaints.count(),

        # Activity
        'activity':           activity,
    }
    return render(request, 'dashboard/owner.html', context)


@tenant_required
def tenant_dashboard(request):
    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint
    from apps.reviews.models import Review

    bookings      = Booking.objects.filter(tenant=request.user).order_by('-created_at')
    agreements    = Agreement.objects.filter(tenant=request.user).order_by('-created_at')
    active_agreement = agreements.filter(status='active').first()

    payments      = Payment.objects.filter(tenant=request.user)
    upcoming_rent = payments.filter(status='pending').order_by('due_date').first()
    overdue_payments = payments.filter(status='overdue').count()

    complaints    = Complaint.objects.filter(tenant=request.user).order_by('-created_at')

    # Activity feed
    activity = []
    for b in bookings[:3]:
        activity.append({
            'icon': '🏠', 'text': f'Booking {b.get_status_display()} — {b.get_target_name()}',
            'time': b.updated_at, 'link': f'/bookings/{b.pk}/'
        })
    for a in agreements[:3]:
        activity.append({
            'icon': '📋', 'text': f'Agreement {a.get_status_display()} — {a.get_target_name()}',
            'time': a.updated_at, 'link': f'/agreements/{a.pk}/'
        })
    for p in payments.order_by('-updated_at')[:3]:
        activity.append({
            'icon': '💰', 'text': f'Payment {p.get_status_display()} — Rs. {p.amount}',
            'time': p.updated_at, 'link': f'/payments/{p.pk}/'
        })
    activity = sorted(activity, key=lambda x: x['time'], reverse=True)[:8]

    context = {
        'active_agreement':   active_agreement,
        'current_property':   bookings.filter(status='accepted').first(),

        'bookings':           bookings[:5],
        'total_bookings':     bookings.count(),
        'pending_bookings':   bookings.filter(status='pending').count(),

        'agreements':         agreements[:3],
        'total_agreements':   agreements.count(),

        'upcoming_rent':      upcoming_rent,
        'overdue_payments':   overdue_payments,
        'total_paid':         payments.filter(status='paid').aggregate(t=Sum('amount'))['t'] or 0,

        'complaints':         complaints[:3],
        'open_complaints':    complaints.filter(status__in=['open','in_progress']).count(),

        'activity':           activity,
    }
    return render(request, 'dashboard/tenant.html', context)