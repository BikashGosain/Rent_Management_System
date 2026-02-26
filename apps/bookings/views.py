from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import Booking
from .forms import BookingRequestForm, OwnerResponseForm
from apps.properties.models import Property, Room


# ── Tenant Views ──────────────────────────────────────────────────────────────

@login_required
def book_property(request, pk):
    """Tenant books a whole property."""
    if not request.user.is_tenant():
        return HttpResponseForbidden('Only tenants can book properties.')

    prop = get_object_or_404(Property, pk=pk, status='available', rent_type='whole')

    # Prevent booking own property
    if prop.owner == request.user:
        messages.error(request, 'You cannot book your own property.')
        return redirect('properties:detail', pk=pk)

    # Prevent duplicate pending booking
    if Booking.objects.filter(tenant=request.user, property=prop, status='pending').exists():
        messages.warning(request, 'You already have a pending booking for this property.')
        return redirect('properties:detail', pk=pk)

    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booking          = form.save(commit=False)
            booking.tenant   = request.user
            booking.property = prop
            booking.save()
            messages.success(request, 'Booking request sent successfully!')
            return redirect('bookings:my_bookings')
    else:
        form = BookingRequestForm()

    return render(request, 'bookings/booking_form.html', {
        'form': form, 'target': prop, 'target_type': 'property'
    })


@login_required
def book_room(request, property_pk, room_pk):
    """Tenant books a room."""
    if not request.user.is_tenant():
        return HttpResponseForbidden('Only tenants can book rooms.')

    room = get_object_or_404(Room, pk=room_pk, property__pk=property_pk, status='available')

    # Prevent booking own room
    if room.property.owner == request.user:
        messages.error(request, 'You cannot book your own property.')
        return redirect('properties:room_detail', pk=property_pk, room_pk=room_pk)

    # Prevent duplicate pending booking
    if Booking.objects.filter(tenant=request.user, room=room, status='pending').exists():
        messages.warning(request, 'You already have a pending booking for this room.')
        return redirect('properties:room_detail', pk=property_pk, room_pk=room_pk)

    if request.method == 'POST':
        form = BookingRequestForm(request.POST)
        if form.is_valid():
            booking        = form.save(commit=False)
            booking.tenant = request.user
            booking.room   = room
            booking.save()
            messages.success(request, 'Booking request sent successfully!')
            return redirect('bookings:my_bookings')
    else:
        form = BookingRequestForm()

    return render(request, 'bookings/booking_form.html', {
        'form': form, 'target': room, 'target_type': 'room'
    })


@login_required
def my_bookings(request):
    """Tenant sees their bookings, but not ones cancelled by owner."""
    if not request.user.is_tenant():
        return redirect('dashboard:owner')

    bookings = Booking.objects.filter(tenant=request.user).select_related(
        'property', 'room', 'room__property'
    ).order_by('-created_at')

    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, pk):
    """Tenant cancels their pending booking."""
    booking = get_object_or_404(Booking, pk=pk, tenant=request.user)

    if not booking.is_pending():
        messages.error(request, 'Only pending bookings can be cancelled.')
        return redirect('bookings:my_bookings')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.cancelled_by = 'tenant'
        booking.save()
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('bookings:my_bookings')

    return render(request, 'bookings/booking_cancel_confirm.html', {'booking': booking})


# ── Owner Views ───────────────────────────────────────────────────────────────

@login_required
def owner_bookings(request):
    """Owner sees all booking requests for their properties."""
    if not request.user.is_owner():
        return redirect('dashboard:tenant')

    bookings = Booking.objects.filter(
        property__owner=request.user
    ).select_related('tenant', 'property', 'room', 'room__property') | Booking.objects.filter(
        room__property__owner=request.user
    ).select_related('tenant', 'property', 'room', 'room__property')

    bookings = bookings.order_by('-created_at')

    return render(request, 'bookings/owner_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    """Owner or tenant views booking detail."""
    booking = get_object_or_404(Booking, pk=pk)

    # Only owner or tenant can view
    is_owner  = booking.get_owner() == request.user
    is_tenant = booking.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden('Access denied.')

    # Determine cancel info
    cancelled_by_owner  = booking.status == 'cancelled' and booking.cancelled_by == 'owner'
    cancelled_by_tenant = booking.status == 'cancelled' and booking.cancelled_by == 'tenant'

    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'is_owner': is_owner,
        'is_tenant': is_tenant,
        'cancelled_by_owner': cancelled_by_owner,
        'cancelled_by_tenant': cancelled_by_tenant,
    })


@login_required
def accept_booking(request, pk):
    """Owner accepts a booking."""
    booking = get_object_or_404(Booking, pk=pk)

    if booking.get_owner() != request.user:
        return HttpResponseForbidden('Access denied.')

    if not booking.is_pending():
        messages.error(request, 'Only pending bookings can be accepted.')
        return redirect('bookings:owner_bookings')

    if request.method == 'POST':
        form = OwnerResponseForm(request.POST, instance=booking)
        if form.is_valid():
            booking        = form.save(commit=False)
            booking.status = 'accepted'
            booking.save()

            # Mark property/room as occupied
            if booking.room:
                booking.room.status = 'occupied'
                booking.room.save()
            elif booking.property:
                booking.property.status = 'occupied'
                booking.property.save()

            messages.success(request, 'Booking accepted!')
            return redirect('bookings:owner_bookings')
    else:
        form = OwnerResponseForm(instance=booking)

    return render(request, 'bookings/booking_respond.html', {
        'form': form, 'booking': booking, 'action': 'Accept'
    })


@login_required
def reject_booking(request, pk):
    """Owner rejects a booking."""
    booking = get_object_or_404(Booking, pk=pk)

    if booking.get_owner() != request.user:
        return HttpResponseForbidden('Access denied.')

    if not booking.is_pending():
        messages.error(request, 'Only pending bookings can be rejected.')
        return redirect('bookings:owner_bookings')

    if request.method == 'POST':
        form = OwnerResponseForm(request.POST, instance=booking)
        if form.is_valid():
            booking        = form.save(commit=False)
            booking.status = 'rejected'
            booking.cancelled_by = 'owner'
            booking.save()
            messages.success(request, 'Booking rejected.')
            return redirect('bookings:owner_bookings')
    else:
        form = OwnerResponseForm(instance=booking)

    return render(request, 'bookings/booking_respond.html', {
        'form': form, 'booking': booking, 'action': 'Reject'
    })


@login_required
def owner_cancel_booking(request, pk):
    """Owner cancels an accepted booking."""
    booking = get_object_or_404(Booking, pk=pk)

    if booking.get_owner() != request.user:
        return HttpResponseForbidden('Access denied.')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.cancelled_by = 'owner'
        booking.save()

        # Mark property/room back to available
        if booking.room:
            booking.room.status = 'available'
            booking.room.save()
        elif booking.property:
            booking.property.status = 'available'
            booking.property.save()

        messages.success(request, 'Booking cancelled.')
        return redirect('bookings:owner_bookings')

    return render(request, 'bookings/booking_cancel_confirm.html', {'booking': booking})