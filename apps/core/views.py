from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from apps.properties.models import Property
from apps.accounts.models import User
from apps.reviews.models import Review


def home(request):
    # Stats
    total_properties = Property.objects.filter(status="available").count()
    total_owners = User.objects.filter(role="owner").count()
    total_tenants = User.objects.filter(role="tenant").count()

    # Featured properties (latest 6 available)
    featured_whole = (
        Property.objects.filter(status="available", rent_type="whole")
        .prefetch_related("photos")
        .order_by("-created_at")[:3]
    )

    featured_rooms = (
        Property.objects.filter(status="available", rent_type="rooms")
        .prefetch_related("photos", "rooms")
        .order_by("-created_at")[:3]
    )

    # Latest reviews with ratings
    testimonials = (
        Review.objects.filter(review_type="property")
        .select_related("reviewer", "property")
        .order_by("-created_at")[:6]
    )

    return render(
        request,
        "core/home.html",
        {
            "total_properties": total_properties,
            "total_owners": total_owners,
            "total_tenants": total_tenants,
            "featured_whole": featured_whole,
            "featured_rooms": featured_rooms,
            "testimonials": testimonials,
        },
    )


@login_required
def recycle_bin(request):
    """Show all soft deleted items for the current user."""
    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    is_owner = request.user.is_owner()
    is_tenant = request.user.is_tenant()

    if is_owner:
        deleted_bookings = Booking.all_objects.filter(owner_deleted=True).filter(
            property__owner=request.user
        ) | Booking.all_objects.filter(
            owner_deleted=True, room__property__owner=request.user
        )
        deleted_agreements = Agreement.all_objects.filter(
            owner=request.user, owner_deleted=True
        )
        deleted_payments = Payment.all_objects.filter(
            owner=request.user, owner_deleted=True
        )
        deleted_complaints = Complaint.all_objects.filter(
            owner=request.user, owner_deleted=True
        )

    elif is_tenant:
        deleted_bookings = Booking.all_objects.filter(
            tenant=request.user, tenant_deleted=True
        )
        deleted_agreements = Agreement.all_objects.filter(
            tenant=request.user, tenant_deleted=True
        )
        deleted_payments = Payment.all_objects.filter(
            tenant=request.user, tenant_deleted=True
        )
        deleted_complaints = Complaint.all_objects.filter(
            tenant=request.user, tenant_deleted=True
        )

    else:
        return HttpResponseForbidden("Access denied.")

    total_deleted = (
        deleted_bookings.count()
        + deleted_agreements.count()
        + deleted_payments.count()
        + deleted_complaints.count()
    )

    return render(
        request,
        "core/recycle_bin.html",
        {
            "deleted_bookings": deleted_bookings,
            "deleted_agreements": deleted_agreements,
            "deleted_payments": deleted_payments,
            "deleted_complaints": deleted_complaints,
            "total_deleted": total_deleted,
            "is_owner": is_owner,
            "is_tenant": is_tenant,
        },
    )


@login_required
def restore_item(request, model, pk):
    if request.method != "POST":
        return redirect("core:recycle_bin")

    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    model_map = {
        "booking": Booking,
        "agreement": Agreement,
        "payment": Payment,
        "complaint": Complaint,
    }

    if model not in model_map:
        return HttpResponseForbidden("Invalid model.")

    obj = get_object_or_404(model_map[model].all_objects, pk=pk)

    # Check ownership correctly for each model
    if model == "booking":
        is_owner = obj.get_owner() == request.user
        is_tenant = obj.tenant == request.user
    elif model == "payment":
        is_owner = obj.owner == request.user
        is_tenant = obj.tenant == request.user
    else:
        # agreement, complaint
        is_owner = obj.owner == request.user
        is_tenant = obj.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if is_owner:
        obj.restore_owner()
    else:
        obj.restore_tenant()

    messages.success(request, f"{model.title()} restored successfully!")
    return redirect("core:recycle_bin")


@login_required
def permanent_delete(request, model, pk):
    if request.method != "POST":
        return redirect("core:recycle_bin")

    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    model_map = {
        "booking": Booking,
        "agreement": Agreement,
        "payment": Payment,
        "complaint": Complaint,
    }

    if model not in model_map:
        return HttpResponseForbidden("Invalid model.")

    obj = get_object_or_404(model_map[model].all_objects, pk=pk)

    # Check ownership correctly for each model
    if model == "booking":
        is_owner = obj.get_owner() == request.user
        is_tenant = obj.tenant == request.user
    elif model == "payment":
        is_owner = obj.owner == request.user
        is_tenant = obj.tenant == request.user
    else:
        # agreement, complaint
        is_owner = obj.owner == request.user
        is_tenant = obj.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    obj.delete()
    messages.success(request, f"{model.title()} permanently deleted.")
    return redirect("core:recycle_bin")


@login_required
def restore_all(request):
    if request.method != "POST":
        return redirect("core:recycle_bin")

    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    is_owner = request.user.is_owner()
    is_tenant = request.user.is_tenant()

    if is_owner:
        Booking.all_objects.filter(
            owner_deleted=True, property__owner=request.user
        ).update(owner_deleted=False, owner_deleted_at=None)
        Booking.all_objects.filter(
            owner_deleted=True, room__property__owner=request.user
        ).update(owner_deleted=False, owner_deleted_at=None)
        Agreement.all_objects.filter(owner=request.user, owner_deleted=True).update(
            owner_deleted=False, owner_deleted_at=None
        )
        Payment.all_objects.filter(owner=request.user, owner_deleted=True).update(
            owner_deleted=False, owner_deleted_at=None
        )
        Complaint.all_objects.filter(owner=request.user, owner_deleted=True).update(
            owner_deleted=False, owner_deleted_at=None
        )

    elif is_tenant:
        Booking.all_objects.filter(tenant=request.user, tenant_deleted=True).update(
            tenant_deleted=False, tenant_deleted_at=None
        )
        Agreement.all_objects.filter(tenant=request.user, tenant_deleted=True).update(
            tenant_deleted=False, tenant_deleted_at=None
        )
        Payment.all_objects.filter(tenant=request.user, tenant_deleted=True).update(
            tenant_deleted=False, tenant_deleted_at=None
        )
        Complaint.all_objects.filter(tenant=request.user, tenant_deleted=True).update(
            tenant_deleted=False, tenant_deleted_at=None
        )

    messages.success(request, "All items restored successfully!")
    return redirect("core:recycle_bin")


@login_required
def permanent_delete_all(request):
    if request.method != "POST":
        return redirect("core:recycle_bin")

    from apps.bookings.models import Booking
    from apps.agreements.models import Agreement
    from apps.payments.models import Payment
    from apps.complaints.models import Complaint

    is_owner = request.user.is_owner()
    is_tenant = request.user.is_tenant()

    if is_owner:
        Booking.all_objects.filter(
            owner_deleted=True, property__owner=request.user
        ).delete()
        Booking.all_objects.filter(
            owner_deleted=True, room__property__owner=request.user
        ).delete()
        Agreement.all_objects.filter(owner=request.user, owner_deleted=True).delete()
        Payment.all_objects.filter(owner=request.user, owner_deleted=True).delete()
        Complaint.all_objects.filter(owner=request.user, owner_deleted=True).delete()

    elif is_tenant:
        Booking.all_objects.filter(tenant=request.user, tenant_deleted=True).delete()
        Agreement.all_objects.filter(tenant=request.user, tenant_deleted=True).delete()
        Payment.all_objects.filter(tenant=request.user, tenant_deleted=True).delete()
        Complaint.all_objects.filter(tenant=request.user, tenant_deleted=True).delete()

    messages.success(request, "All items permanently deleted.")
    return redirect("core:recycle_bin")
