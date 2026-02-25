from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Property, Room
from .forms import PropertyForm, PropertyPhotoFormSet, RoomForm, RoomPhotoFormSet


# ── Property Views ────────────────────────────────────────────────────────────

@login_required
def property_list(request):
    if not request.user.is_owner():
        return redirect('dashboard:tenant')
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'properties/property_list.html', {'properties': properties})


@login_required
def property_add(request):
    if not request.user.is_owner():
        return redirect('dashboard:tenant')

    if request.method == 'POST':
        form    = PropertyForm(request.POST)
        formset = PropertyPhotoFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            prop       = form.save(commit=False)
            prop.owner = request.user
            prop.save()
            formset.instance = prop
            formset.save()
            messages.success(request, 'Property added successfully!')
            if prop.is_rooms():
                messages.info(request, 'Now add rooms to your property.')
                return redirect('properties:room_add', pk=prop.pk)
            return redirect('properties:list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = PropertyForm()
        formset = PropertyPhotoFormSet()

    return render(request, 'properties/property_form.html', {
        'form': form, 'formset': formset, 'action': 'Add'
    })


@login_required
def property_edit(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        form    = PropertyForm(request.POST, instance=prop)
        formset = PropertyPhotoFormSet(request.POST, request.FILES, instance=prop)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('properties:detail', pk=prop.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = PropertyForm(instance=prop)
        formset = PropertyPhotoFormSet(instance=prop)

    return render(request, 'properties/property_form.html', {
        'form': form, 'formset': formset, 'action': 'Edit'
    })


@login_required
def property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        prop.delete()
        messages.success(request, 'Property deleted.')
        return redirect('properties:list')
    return render(request, 'properties/property_confirm_delete.html', {'property': prop})


@login_required
def property_detail(request, pk):
    prop  = get_object_or_404(Property, pk=pk)
    rooms = prop.rooms.all() if prop.is_rooms() else None
    photos = prop.photos.all()
    return render(request, 'properties/property_detail.html', {
        'property': prop, 'rooms': rooms, 'photos': photos
    })


# ── Room Views ────────────────────────────────────────────────────────────────

@login_required
def room_add(request, pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        form    = RoomForm(request.POST)
        formset = RoomPhotoFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            room          = form.save(commit=False)
            room.property = prop
            room.save()
            formset.instance = room
            formset.save()
            messages.success(request, f'Room {room.room_number} added successfully!')
            return redirect('properties:detail', pk=prop.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = RoomForm()
        formset = RoomPhotoFormSet()

    return render(request, 'properties/room_form.html', {
        'form': form, 'formset': formset, 'property': prop, 'action': 'Add'
    })


@login_required
def room_edit(request, pk, room_pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    room = get_object_or_404(Room, pk=room_pk, property=prop)

    if request.method == 'POST':
        form    = RoomForm(request.POST, instance=room)
        formset = RoomPhotoFormSet(request.POST, request.FILES, instance=room)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Room {room.room_number} updated!')
            return redirect('properties:detail', pk=prop.pk)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form    = RoomForm(instance=room)
        formset = RoomPhotoFormSet(instance=room)

    return render(request, 'properties/room_form.html', {
        'form': form, 'formset': formset, 'property': prop, 'action': 'Edit'
    })


@login_required
def room_delete(request, pk, room_pk):
    prop = get_object_or_404(Property, pk=pk, owner=request.user)
    room = get_object_or_404(Room, pk=room_pk, property=prop)
    if request.method == 'POST':
        room.delete()
        messages.success(request, f'Room {room.room_number} deleted.')
        return redirect('properties:detail', pk=prop.pk)
    return render(request, 'properties/room_confirm_delete.html', {
        'room': room, 'property': prop
    })


@login_required
def room_detail(request, pk, room_pk):
    prop = get_object_or_404(Property, pk=pk)
    room = get_object_or_404(Room, pk=room_pk, property=prop)
    photos = room.photos.all()
    return render(request, 'properties/room_detail.html', {
        'property': prop, 'room': room, 'photos': photos
    })