from django.shortcuts import render, redirect, get_object_or_404
import os
from django.http import FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Agreement
from .forms import (
    AgreementForm,
    NoticeForm,
    NoticeResponseForm,
    ExtensionRequestForm,
    ExtensionResponseForm,
)

from apps.notifications.utils import (
    notify_agreement_created,
    notify_agreement_signed,
    notify_agreement_terminated,
)


@login_required
def create_agreement(request, booking_pk):
    from apps.bookings.models import Booking

    if not request.user.is_owner():
        return HttpResponseForbidden("Only owners can create agreements.")

    booking = get_object_or_404(Booking, pk=booking_pk, status="accepted")

    if request.method == "POST":
        form = AgreementForm(request.POST, request.FILES)
        if form.is_valid():
            agreement = form.save(commit=False)
            agreement.owner = request.user
            agreement.tenant = booking.tenant
            agreement.booking = booking
            if booking.room:
                agreement.room = booking.room
            elif booking.property:
                agreement.property = booking.property

            # Calculate end date for short term
            if agreement.rental_type == "short":
                agreement.end_date = agreement.calculate_short_term_end_date()

            agreement.save()
            notify_agreement_created(agreement)
            messages.success(request, "Agreement created successfully!")
            return redirect("agreements:detail", pk=agreement.pk)
    else:
        initial = {
            "rent_amount": booking.get_rent_price(),
            "start_date": booking.move_in_date,
            "rental_type": "fixed",
        }
        if booking.move_out_date:
            initial["end_date"] = booking.move_out_date
        form = AgreementForm(initial=initial)

    return render(
        request, "agreements/agreement_form.html", {"form": form, "booking": booking}
    )


@login_required
def owner_agreements(request):
    if not request.user.is_owner():
        return redirect("dashboard:tenant")
    agreements = Agreement.owner_objects.filter(owner=request.user)
    return render(
        request, "agreements/owner_agreements.html", {"agreements": agreements}
    )


@login_required
def tenant_agreements(request):
    if not request.user.is_tenant():
        return redirect("dashboard:owner")
    agreements = Agreement.tenant_objects.filter(tenant=request.user)
    return render(
        request, "agreements/tenant_agreements.html", {"agreements": agreements}
    )


@login_required
def agreement_detail(request, pk):
    agreement = get_object_or_404(Agreement.all_objects, pk=pk)
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user
    is_admin = request.user.is_admin() or request.user.is_superuser

    if not (is_owner or is_tenant or is_admin):
        return HttpResponseForbidden("Access denied.")

    days_remaining = agreement.notice_days_remaining()
    progress = agreement.notice_progress_percent()

    return render(
        request,
        "agreements/agreement_detail.html",
        {
            "agreement": agreement,
            "is_owner": is_owner,
            "is_tenant": is_tenant,
            "days_remaining": days_remaining,
            "progress": progress,
        },
    )


@login_required
def sign_agreement(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        if is_owner and not agreement.owner_signed:
            agreement.owner_signed = True
            agreement.owner_signed_at = timezone.now()
        elif is_tenant and not agreement.tenant_signed:
            agreement.tenant_signed = True
            agreement.tenant_signed_at = timezone.now()

        if agreement.owner_signed and agreement.tenant_signed:
            agreement.status = "active"

            # Mark property/room occupied
            if agreement.room:
                agreement.room.status = "occupied"
                agreement.room.save()
            elif agreement.property:
                agreement.property.status = "occupied"
                agreement.property.save()
        elif agreement.owner_signed:
            agreement.status = "pending_tenant"
        elif agreement.tenant_signed:
            agreement.status = "pending_owner"

        agreement.save()
        notify_agreement_signed(agreement, signed_by=request.user)
        messages.success(request, "Agreement signed successfully!")
        return redirect("agreements:detail", pk=pk)

    return render(request, "agreements/sign_confirm.html", {"agreement": agreement})


@login_required
def terminate_agreement(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if not agreement.is_active():
        messages.error(request, "Only active agreements can be terminated.")
        return redirect("agreements:detail", pk=pk)

    if request.method == "POST":
        reason = request.POST.get("termination_reason", "")
        agreement.status = "terminated"
        agreement.terminated_by = request.user
        agreement.terminated_at = timezone.now()
        agreement.termination_reason = reason

        if agreement.room:
            agreement.room.status = "available"
            agreement.room.save()
        elif agreement.property:
            agreement.property.status = "available"
            agreement.property.save()

        agreement.save()
        notify_agreement_terminated(agreement, terminated_by=request.user)
        messages.success(request, "Agreement terminated.")
        return redirect("agreements:detail", pk=pk)

    return render(
        request, "agreements/terminate_confirm.html", {"agreement": agreement}
    )


# ── Notice Views ──────────────────────────────────────────────────────────────


@login_required
def submit_notice(request, pk):
    """Tenant or owner submits a notice."""
    agreement = get_object_or_404(Agreement, pk=pk, status="active")
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if agreement.notice_status not in ["none", "rejected"]:
        messages.error(request, "A notice is already active for this agreement.")
        return redirect("agreements:detail", pk=pk)

    if request.method == "POST":
        form = NoticeForm(request.POST, instance=agreement)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.notice_status = "pending"
            notice.notice_given_by = request.user
            notice.notice_given_at = timezone.now()

            # Auto calculate vacate date if not set
            if not notice.notice_vacate_date:
                notice.notice_vacate_date = timezone.now().date() + __import__(
                    "datetime"
                ).timedelta(days=agreement.notice_period_days)

            # Restrict notice types by role
            if is_tenant and notice.notice_type == "owner_notice":
                notice.notice_type = "vacate"
            if is_owner and notice.notice_type in ["vacate", "early_term"]:
                notice.notice_type = "owner_notice"

            notice.save()

            # Notify other party
            from apps.notifications.utils import send_notification

            if is_tenant:
                send_notification(
                    recipient=agreement.owner,
                    notif_type="agreement_signed",
                    title="📢 Tenant Submitted Notice",
                    message=f"{agreement.tenant.get_full_name() or agreement.tenant.username} has submitted a notice for {agreement.get_target_name()}. Vacate date: {notice.notice_vacate_date}",
                    link=f"/agreements/{agreement.pk}/",
                )
            else:
                send_notification(
                    recipient=agreement.tenant,
                    notif_type="agreement_signed",
                    title="📢 Owner Submitted Notice",
                    message=f"Your owner has submitted a notice for {agreement.get_target_name()}. Vacate date: {notice.notice_vacate_date}",
                    link=f"/agreements/{agreement.pk}/",
                )

            messages.success(request, "Notice submitted successfully!")
            return redirect("agreements:detail", pk=pk)
    else:
        # Pre-fill notice type based on role
        initial = {}
        if is_tenant:
            initial["notice_type"] = "vacate"
            initial["notice_vacate_date"] = timezone.now().date() + __import__(
                "datetime"
            ).timedelta(days=agreement.notice_period_days)
        else:
            initial["notice_type"] = "owner_notice"
            initial["notice_vacate_date"] = timezone.now().date() + __import__(
                "datetime"
            ).timedelta(days=agreement.notice_period_days)
        form = NoticeForm(instance=agreement, initial=initial)

    return render(
        request,
        "agreements/notice_form.html",
        {
            "form": form,
            "agreement": agreement,
            "is_owner": is_owner,
            "is_tenant": is_tenant,
        },
    )


@login_required
def respond_notice(request, pk):
    """Owner responds to tenant notice."""
    agreement = get_object_or_404(Agreement, pk=pk, owner=request.user)

    if agreement.notice_status != "pending":
        messages.error(request, "No pending notice to respond to.")
        return redirect("agreements:detail", pk=pk)

    if request.method == "POST":
        form = NoticeResponseForm(request.POST, instance=agreement)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.notice_responded_at = timezone.now()

            # If approved or mutual — terminate agreement on vacate date
            if notice.notice_status in ["approved", "mutual"]:
                from apps.notifications.utils import send_notification

                send_notification(
                    recipient=agreement.tenant,
                    notif_type="agreement_terminated",
                    title="✅ Notice Approved",
                    message=f"Your notice for {agreement.get_target_name()} has been approved. Vacate by {agreement.notice_vacate_date}.",
                    link=f"/agreements/{agreement.pk}/",
                )
            elif notice.notice_status == "rejected":
                from apps.notifications.utils import send_notification

                send_notification(
                    recipient=agreement.tenant,
                    notif_type="agreement_terminated",
                    title="❌ Notice Rejected",
                    message=f"Your notice for {agreement.get_target_name()} has been rejected. Reason: {notice.notice_response}",
                    link=f"/agreements/{agreement.pk}/",
                )

            notice.save()
            messages.success(request, "Notice response submitted.")
            return redirect("agreements:detail", pk=pk)
    else:
        form = NoticeResponseForm(instance=agreement)

    return render(
        request,
        "agreements/notice_response_form.html",
        {"form": form, "agreement": agreement},
    )


@login_required
def cancel_notice(request, pk):
    """Cancel a pending notice."""
    agreement = get_object_or_404(Agreement, pk=pk)
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if request.method == "POST":
        agreement.notice_status = "none"
        agreement.notice_given_by = None
        agreement.notice_given_at = None
        agreement.notice_vacate_date = None
        agreement.notice_reason = ""
        agreement.notice_type = ""
        agreement.notice_response = ""
        agreement.notice_responded_at = None
        agreement.save()
        messages.success(request, "Notice cancelled.")

    return redirect("agreements:detail", pk=pk)


@login_required
def complete_vacate(request, pk):
    """Mark tenant as vacated after notice period ends."""
    agreement = get_object_or_404(Agreement, pk=pk, owner=request.user)

    if request.method == "POST":
        agreement.status = "terminated"
        agreement.terminated_by = request.user
        agreement.terminated_at = timezone.now()
        agreement.termination_reason = (
            f"Vacated as per notice. Vacate date: {agreement.notice_vacate_date}"
        )

        if agreement.room:
            agreement.room.status = "available"
            agreement.room.save()
        elif agreement.property:
            agreement.property.status = "available"
            agreement.property.save()

        agreement.save()

        from apps.notifications.utils import send_notification

        send_notification(
            recipient=agreement.tenant,
            notif_type="agreement_terminated",
            title="🏠 Vacate Completed",
            message=f"Your tenancy for {agreement.get_target_name()} has been marked as completed.",
            link=f"/agreements/{agreement.pk}/",
        )
        messages.success(
            request, "Tenant marked as vacated. Property is now available."
        )

    return redirect("agreements:detail", pk=pk)


@login_required
def request_extension(request, pk):
    """Tenant or owner requests extension of stay."""
    agreement = get_object_or_404(Agreement, pk=pk, status="active")
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    if agreement.extension_status == "pending":
        messages.error(request, "An extension request is already pending.")
        return redirect("agreements:detail", pk=pk)

    if request.method == "POST":
        form = ExtensionRequestForm(request.POST, instance=agreement)
        if form.is_valid():
            ext = form.save(commit=False)
            ext.extension_status = "pending"
            ext.extension_requested_by = request.user
            ext.extension_requested_at = timezone.now()
            ext.extension_new_end_date = ext.calculate_extension_end_date()
            ext.save()

            # Notify other party
            from apps.notifications.utils import send_notification

            if is_tenant:
                send_notification(
                    recipient=agreement.owner,
                    notif_type="agreement_signed",
                    title="📅 Extension Request Received",
                    message=f"{agreement.tenant.get_full_name() or agreement.tenant.username} wants to extend stay by {ext.extension_duration} {ext.extension_unit} at {agreement.get_target_name()}. New end date: {ext.extension_new_end_date}",
                    link=f"/agreements/{agreement.pk}/",
                )
            else:
                send_notification(
                    recipient=agreement.tenant,
                    notif_type="agreement_signed",
                    title="📅 Owner Proposes Extension",
                    message=f"Owner is proposing to extend your stay by {ext.extension_duration} {ext.extension_unit} at {agreement.get_target_name()}. New end date: {ext.extension_new_end_date}",
                    link=f"/agreements/{agreement.pk}/",
                )

            messages.success(
                request,
                f"Extension request submitted! New end date would be {ext.extension_new_end_date}.",
            )
            return redirect("agreements:detail", pk=pk)
    else:
        form = ExtensionRequestForm()

    return render(
        request,
        "agreements/extension_request_form.html",
        {
            "form": form,
            "agreement": agreement,
            "is_owner": is_owner,
            "is_tenant": is_tenant,
        },
    )


@login_required
def respond_extension(request, pk):
    """Owner or tenant responds to extension request."""
    agreement = get_object_or_404(Agreement, pk=pk)

    # The other party responds
    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    # Requester cannot respond to their own request
    if agreement.extension_requested_by == request.user:
        messages.error(request, "You cannot respond to your own extension request.")
        return redirect("agreements:detail", pk=pk)

    if agreement.extension_status != "pending":
        messages.error(request, "No pending extension request.")
        return redirect("agreements:detail", pk=pk)

    if request.method == "POST":
        form = ExtensionResponseForm(request.POST, instance=agreement)
        if form.is_valid():
            ext = form.save(commit=False)
            ext.extension_responded_at = timezone.now()
            ext.extension_responded_by = request.user

            if ext.extension_status == "approved":
                # Update the actual end date
                # old_end = agreement.end_date
                ext.end_date = ext.extension_new_end_date

                from apps.notifications.utils import send_notification

                notify_user = agreement.tenant if is_owner else agreement.owner
                send_notification(
                    recipient=notify_user,
                    notif_type="agreement_signed",
                    title="✅ Extension Approved!",
                    message=f"Your extension request for {agreement.get_target_name()} has been approved. New end date: {ext.extension_new_end_date}",
                    link=f"/agreements/{agreement.pk}/",
                )
            elif ext.extension_status == "rejected":
                from apps.notifications.utils import send_notification

                notify_user = agreement.tenant if is_owner else agreement.owner
                send_notification(
                    recipient=notify_user,
                    notif_type="agreement_signed",
                    title="❌ Extension Rejected",
                    message=f"Your extension request for {agreement.get_target_name()} has been rejected. Reason: {ext.extension_response}",
                    link=f"/agreements/{agreement.pk}/",
                )

            ext.save()
            messages.success(request, f"Extension request {ext.extension_status}.")
            return redirect("agreements:detail", pk=pk)
    else:
        form = ExtensionResponseForm(instance=agreement)

    return render(
        request,
        "agreements/extension_response_form.html",
        {
            "form": form,
            "agreement": agreement,
        },
    )


@login_required
def cancel_extension(request, pk):
    """Cancel a pending extension request."""
    agreement = get_object_or_404(Agreement, pk=pk)

    if agreement.extension_requested_by != request.user:
        return HttpResponseForbidden("Only the requester can cancel.")

    if request.method == "POST":
        agreement.extension_status = "none"
        agreement.extension_requested_by = None
        agreement.extension_requested_at = None
        agreement.extension_duration = None
        agreement.extension_unit = ""
        agreement.extension_reason = ""
        agreement.extension_new_end_date = None
        agreement.extension_response = ""
        agreement.extension_responded_at = None
        agreement.extension_responded_by = None
        agreement.save()
        messages.success(request, "Extension request cancelled.")

    return redirect("agreements:detail", pk=pk)


@login_required
def delete_agreement(request, pk):
    agreement = get_object_or_404(Agreement.all_objects, pk=pk)

    is_owner = agreement.owner == request.user
    is_tenant = agreement.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden("Access denied.")

    allowed = ["terminated", "expired"]
    if agreement.status not in allowed:
        messages.error(request, "Cannot delete an active agreement.")
        return redirect(
            "agreements:owner_agreements"
            if is_owner
            else "agreements:tenant_agreements"
        )

    if request.method == "POST":
        if is_owner:
            agreement.soft_delete_by_owner()
        else:
            agreement.soft_delete_by_tenant()
        messages.success(request, "Agreement removed from your list.")
        if is_owner:
            return redirect("agreements:owner_agreements")
        return redirect("agreements:tenant_agreements")

    return render(
        request, "base_delete_confirm.html", {"object": agreement, "type": "Agreement"}
    )


@login_required
def download_agreement_document(request, pk):
    agreement = get_object_or_404(Agreement, pk=pk)

    # Only owner or tenant can download
    if request.user != agreement.owner and request.user != agreement.tenant:
        return HttpResponseForbidden("Access denied.")

    if not agreement.document:
        raise Http404("No document uploaded.")

    file_path = agreement.document.path

    if not os.path.exists(file_path):
        raise Http404("File not found.")

    # Force download — browser won't open inline
    response = FileResponse(
        open(file_path, "rb"),
        as_attachment=True,  # ← this forces download
        filename=os.path.basename(file_path),  # ← original filename
    )
    return response


@login_required
def edit_agreement(request, pk):
    """Owner edits agreement — mainly to upload document."""
    agreement = get_object_or_404(Agreement, pk=pk, owner=request.user)

    if not request.user.is_owner():
        return HttpResponseForbidden("Only owners can edit agreements.")

    if request.method == "POST":
        form = AgreementForm(request.POST, request.FILES, instance=agreement)
        if form.is_valid():
            form.save()
            messages.success(request, "Agreement updated successfully!")
            return redirect("agreements:detail", pk=pk)
    else:
        form = AgreementForm(instance=agreement)

    return render(
        request,
        "agreements/agreement_form.html",
        {
            "form": form,
            "agreement": agreement,
            "is_edit": True,
            "booking": agreement.booking,
        },
    )
