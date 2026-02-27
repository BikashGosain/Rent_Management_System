from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Agreement
from .forms import AgreementForm
from apps.bookings.models import Booking

from apps.notifications.utils import (
    notify_agreement_created,
    notify_agreement_signed,
    notify_agreement_terminated,
)


# ── Owner Views ───────────────────────────────────────────────────────────────

@login_required
def create_agreement(request, booking_pk):
    """Owner creates agreement after booking is accepted."""
    if not request.user.is_owner():
        return HttpResponseForbidden('Only owners can create agreements.')

    booking = get_object_or_404(Booking, pk=booking_pk)

    if booking.get_owner() != request.user:
        return HttpResponseForbidden('Access denied.')

    if not booking.is_accepted():
        messages.error(request, 'Agreement can only be created for accepted bookings.')
        return redirect('bookings:owner_bookings')

    # Prevent duplicate agreement
    last_agreement = booking.agreements.last()
    if last_agreement and last_agreement.status != 'terminated':
        messages.warning(request, 'Agreement already exists for this booking.')
        return redirect('agreements:detail', pk=last_agreement.pk)

    if request.method == 'POST':
        form = AgreementForm(request.POST, request.FILES)
        if form.is_valid():
            agreement         = form.save(commit=False)
            agreement.owner   = request.user
            agreement.tenant  = booking.tenant
            agreement.booking = booking
            if booking.room:
                agreement.room = booking.room
            else:
                agreement.property = booking.property
            agreement.save()
            notify_agreement_created(agreement)
            messages.success(request, 'Agreement created! Waiting for your signature.')
            return redirect('agreements:detail', pk=agreement.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        # Pre-fill rent from booking
        initial = {}
        if booking.room:
            initial['rent_amount']      = booking.room.rent_price
            initial['security_deposit'] = booking.room.security_deposit or 0
            initial['advance_amount']   = (booking.room.rent_price or 0) * (booking.room.advance_months or 1)
        elif booking.property:
            initial['rent_amount']      = booking.property.rent_price
            initial['security_deposit'] = booking.property.security_deposit or 0
            initial['advance_amount']   = (booking.property.rent_price or 0) * (booking.property.advance_months or 1)
        initial['start_date'] = booking.move_in_date
        initial['end_date']   = booking.move_out_date
        form = AgreementForm(initial=initial)

    return render(request, 'agreements/agreement_form.html', {
        'form': form, 'booking': booking
    })


@login_required
def owner_agreements(request):
    """Owner sees all their agreements."""
    if not request.user.is_owner():
        return redirect('dashboard:tenant')
    agreements = Agreement.objects.filter(owner=request.user).select_related('tenant', 'property', 'room')
    return render(request, 'agreements/owner_agreements.html', {'agreements': agreements})


# ── Tenant Views ──────────────────────────────────────────────────────────────

@login_required
def tenant_agreements(request):
    """Tenant sees all their agreements."""
    if not request.user.is_tenant():
        return redirect('dashboard:owner')
    agreements = Agreement.objects.filter(tenant=request.user).select_related('owner', 'property', 'room')
    return render(request, 'agreements/tenant_agreements.html', {'agreements': agreements})


# ── Shared Views ──────────────────────────────────────────────────────────────

@login_required
def agreement_detail(request, pk):
    """Owner or tenant views agreement detail."""
    agreement = get_object_or_404(Agreement, pk=pk)

    is_owner  = agreement.owner  == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden('Access denied.')

    return render(request, 'agreements/agreement_detail.html', {
        'agreement': agreement,
        'is_owner':  is_owner,
        'is_tenant': is_tenant,
    })


@login_required
def sign_agreement(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    is_owner  = agreement.owner  == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden('Access denied.')

    if request.method == 'POST':
        now = timezone.now()

        if is_owner and not agreement.owner_signed:
            agreement.owner_signed    = True
            agreement.owner_signed_at = now
            messages.success(request, 'You have signed the agreement.')

        elif is_tenant and not agreement.tenant_signed:
            agreement.tenant_signed    = True
            agreement.tenant_signed_at = now
            messages.success(request, 'You have signed the agreement.')

        else:
            messages.warning(request, 'You have already signed this agreement.')
            return redirect('agreements:detail', pk=agreement.pk)

        # ← Check AFTER saving both signatures
        if agreement.owner_signed and agreement.tenant_signed:
            agreement.status = 'active'
            messages.success(request, 'Agreement is now ACTIVE! Both parties have signed.')
        elif is_owner:
            agreement.status = 'pending_tenant'
        elif is_tenant:
            agreement.status = 'pending_owner'

        agreement.save()
        notify_agreement_signed(agreement, signed_by=request.user)
        return redirect('agreements:detail', pk=agreement.pk)

    return render(request, 'agreements/sign_confirm.html', {'agreement': agreement})

@login_required
def terminate_agreement(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    is_owner  = agreement.owner  == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden('Access denied.')

    if not agreement.is_active():
        messages.error(request, 'Only active agreements can be terminated.')
        return redirect('agreements:detail', pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        agreement.status             = 'terminated'
        agreement.terminated_by      = request.user
        agreement.terminated_at      = timezone.now()
        agreement.termination_reason = reason
        agreement.save()
        notify_agreement_terminated(agreement, terminated_by=request.user)

        # Mark property/room back to available
        if agreement.room:
            agreement.room.status = 'available'
            agreement.room.save()
        elif agreement.property:
            agreement.property.status = 'available'
            agreement.property.save()

        messages.success(request, 'Agreement terminated successfully.')
        if is_owner:
            return redirect('agreements:owner_agreements')
        return redirect('agreements:tenant_agreements')

    return render(request, 'agreements/terminate_confirm.html', {'agreement': agreement})