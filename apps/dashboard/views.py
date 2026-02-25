from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

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


@owner_required
def owner_dashboard(request):
    context = {
        'properties':        [],  # update when properties app is built
        'pending_bookings':  [],  # update when bookings app is built
        'active_tenants':    [],  # update when bookings app is built
        'recent_payments':   [],  # update when payments app is built
        'open_complaints':   [],  # update when complaints app is built
    }
    return render(request, 'dashboard/owner.html', context)


@tenant_required
def tenant_dashboard(request):
    context = {
        'current_property':  None,  # update when properties app is built
        'booking_status':    None,  # update when bookings app is built
        'upcoming_rent':     None,  # update when payments app is built
        'agreements':        [],    # update when agreements app is built
        'complaints':        [],    # update when complaints app is built
    }
    return render(request, 'dashboard/tenant.html', context)