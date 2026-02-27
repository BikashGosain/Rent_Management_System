from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Complaint, ComplaintResponse
from .forms import ComplaintForm, ComplaintResponseForm, ComplaintStatusForm, OwnerComplaintForm
from apps.agreements.models import Agreement

from apps.notifications.utils import notify_complaint_submitted, notify_complaint_response

# ── Tenant Views ──────────────────────────────────────────────────────────────

@login_required
def submit_complaint(request):
    """Tenant submits a complaint."""
    if not request.user.is_tenant():
        return HttpResponseForbidden('Only tenants can submit complaints.')

    # Get tenant's active agreements to link complaint
    agreements = Agreement.objects.filter(
        tenant=request.user, status='active'
    ).select_related('owner', 'property', 'room')

    if not agreements.exists():
        messages.error(request, 'You need an active agreement to submit a complaint.')
        return redirect('dashboard:tenant')

    if request.method == 'POST':
        form         = ComplaintForm(request.POST, request.FILES)
        agreement_pk = request.POST.get('agreement')

        if form.is_valid() and agreement_pk:
            agreement  = get_object_or_404(Agreement, pk=agreement_pk, tenant=request.user)
            complaint  = form.save(commit=False)
            complaint.tenant    = request.user
            complaint.owner     = agreement.owner
            complaint.agreement = agreement
            if agreement.room:
                complaint.room = agreement.room
            elif agreement.property:
                complaint.property = agreement.property
            complaint.save()
            notify_complaint_submitted(complaint)
            messages.success(request, 'Complaint submitted successfully!')
            return redirect('complaints:my_complaints')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ComplaintForm()

    return render(request, 'complaints/complaint_form.html', {
        'form': form, 'agreements': agreements
    })


@login_required
def my_complaints(request):
    if not request.user.is_tenant():
        return redirect('dashboard:owner')

    # Complaints submitted BY tenant
    my_submitted = Complaint.objects.filter(
        tenant=request.user, submitted_by='tenant'
    ).prefetch_related('responses')

    # Complaints raised AGAINST tenant by owner
    raised_against = Complaint.objects.filter(
        tenant=request.user, submitted_by='owner'
    ).prefetch_related('responses')

    return render(request, 'complaints/my_complaints.html', {
        'my_submitted':   my_submitted,
        'raised_against': raised_against,
    })

# ── Owner Views ───────────────────────────────────────────────────────────────

@login_required
def owner_complaints(request):
    """Owner sees all complaints for their properties."""
    if not request.user.is_owner():
        return redirect('dashboard:tenant')

    complaints = Complaint.objects.filter(
        owner=request.user
    ).prefetch_related('responses').select_related('tenant')

    open_count     = complaints.filter(status='open').count()
    progress_count = complaints.filter(status='in_progress').count()

    return render(request, 'complaints/owner_complaints.html', {
        'complaints':     complaints,
        'open_count':     open_count,
        'progress_count': progress_count,
    })


# ── Shared Views ──────────────────────────────────────────────────────────────

@login_required
def complaint_detail(request, pk):
    """Owner or tenant views complaint detail and responses."""
    complaint = get_object_or_404(Complaint, pk=pk)

    is_owner  = complaint.owner  == request.user
    is_tenant = complaint.tenant == request.user
    is_admin  = request.user.is_admin() or request.user.is_superuser

    if not (is_owner or is_tenant or is_admin):
        return HttpResponseForbidden('Access denied.')

    responses    = complaint.responses.all()
    response_form = ComplaintResponseForm()
    status_form   = ComplaintStatusForm(instance=complaint)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Add response
        if action == 'respond':
            response_form = ComplaintResponseForm(request.POST, request.FILES)
            if response_form.is_valid():
                response           = response_form.save(commit=False)
                response.complaint = complaint
                response.responder = request.user
                response.save()
                notify_complaint_response(complaint, responder=request.user)

                # Auto update status when owner responds
                if is_owner and complaint.status == 'open':
                    complaint.status = 'in_progress'
                    complaint.save()

                messages.success(request, 'Response added successfully!')
                return redirect('complaints:detail', pk=pk)

        # Update status (owner only)
        elif action == 'update_status' and is_owner:
            status_form = ComplaintStatusForm(request.POST, instance=complaint)
            if status_form.is_valid():
                complaint = status_form.save(commit=False)
                if complaint.status in ['resolved', 'closed']:
                    complaint.resolved_at = timezone.now()
                complaint.save()
                messages.success(request, f'Status updated to {complaint.get_status_display()}.')
                return redirect('complaints:detail', pk=pk)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint':     complaint,
        'responses':     responses,
        'response_form': response_form,
        'status_form':   status_form,
        'is_owner':      is_owner,
        'is_tenant':     is_tenant,
        'is_admin':      is_admin,
    })


# ── Admin Views ───────────────────────────────────────────────────────────────

@login_required
def admin_complaints(request):
    """Admin views all complaints."""
    if not (request.user.is_admin() or request.user.is_superuser):
        return HttpResponseForbidden('Access denied.')

    complaints = Complaint.objects.all().select_related(
        'tenant', 'owner', 'property', 'room'
    ).prefetch_related('responses')

    return render(request, 'complaints/admin_complaints.html', {'complaints': complaints})

@login_required
def owner_submit_complaint(request, agreement_pk):
    """Owner submits complaint against a tenant."""
    if not request.user.is_owner():
        return HttpResponseForbidden('Only owners can use this.')

    agreement = get_object_or_404(Agreement, pk=agreement_pk, owner=request.user, status='active')

    if request.method == 'POST':
        form = OwnerComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint              = form.save(commit=False)
            complaint.owner        = request.user
            complaint.tenant       = agreement.tenant
            complaint.agreement    = agreement
            complaint.submitted_by = 'owner'
            if agreement.room:
                complaint.room = agreement.room
            elif agreement.property:
                complaint.property = agreement.property
            complaint.save()
            notify_complaint_submitted(complaint)
            messages.success(request, 'Issue raised against tenant successfully!')
            return redirect('complaints:owner_complaints')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = OwnerComplaintForm()

    return render(request, 'complaints/owner_complaint_form.html', {
        'form': form, 'agreement': agreement
    })