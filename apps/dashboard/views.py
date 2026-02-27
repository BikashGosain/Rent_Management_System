from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from apps.properties.models import Property

from apps.bookings.models import Booking

User = get_user_model()


def admin_required(view_func):
    """Only admin/superuser can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_admin() or request.user.is_superuser):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def owner_required(view_func):
    """Only owners can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_owner():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_required(view_func):
    """Only tenants can access."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_tenant():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    context = {
        'total_users':      User.objects.count(),
        'total_owners':     User.objects.filter(role='owner').count(),
        'total_tenants':    User.objects.filter(role='tenant').count(),
        'total_properties': 0,  # update when properties app is built
        'total_bookings':   0,  # update when bookings app is built
        'total_payments':   0,  # update when payments app is built
        'recent_users':     User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'dashboard/admin.html', context)


from apps.complaints.models import Complaint

@owner_required
def owner_dashboard(request):
    from apps.properties.models import Property
    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    properties       = Property.objects.filter(owner=request.user)
    pending_bookings = Booking.objects.filter(
        property__owner=request.user, status='pending'
    ) | Booking.objects.filter(
        room__property__owner=request.user, status='pending'
    )
    recent_payments = Payment.objects.filter(
        owner=request.user, status='paid'
    ).order_by('-paid_date')[:5]
    open_complaints = Complaint.objects.filter(
        owner=request.user, status__in=['open', 'in_progress']
    )
    context = {
        'properties':       properties,
        'pending_bookings': pending_bookings.order_by('-created_at')[:5],
        'active_tenants':   Agreement.objects.filter(owner=request.user, status='active').count(),
        'recent_payments':  recent_payments,
        'open_complaints':  open_complaints,
    }
    return render(request, 'dashboard/owner.html', context)


@tenant_required
def tenant_dashboard(request):
    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    bookings      = Booking.objects.filter(tenant=request.user).order_by('-created_at')
    agreements    = Agreement.objects.filter(tenant=request.user).order_by('-created_at')
    upcoming_rent = Payment.objects.filter(
        tenant=request.user, status='pending'
    ).order_by('due_date').first()
    complaints = Complaint.objects.filter(tenant=request.user).order_by('-created_at')[:3]
    context = {
        'current_property': bookings.filter(status='accepted').first(),
        'booking_status':   bookings.first(),
        'upcoming_rent':    upcoming_rent,
        'agreements':       agreements[:3],
        'complaints':       complaints,
    }
    return render(request, 'dashboard/tenant.html', context)