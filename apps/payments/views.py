from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import Payment
from .forms import PaymentCreateForm, PaymentMarkPaidForm
from .utils import generate_monthly_payments
from apps.agreements.models import Agreement


# ── Owner Views ───────────────────────────────────────────────────────────────

@login_required
def owner_payments(request):
    """Owner sees all payments for their properties."""
    if not request.user.is_owner():
        return redirect('dashboard:tenant')
    payments = Payment.owner_objects.filter(owner=request.user).select_related(
        'tenant', 'agreement'
    )
    # Update overdue status
    for payment in payments:
        if payment.is_overdue():
            payment.status = 'overdue'
            payment.save()

    total_received = payments.filter(status='paid').aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('amount')
    )['total'] or 0
    total_pending = payments.filter(status__in=['pending', 'overdue']).aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('amount')
    )['total'] or 0

    return render(request, 'payments/owner_payments.html', {
        'payments':       payments,
        'total_received': total_received,
        'total_pending':  total_pending,
    })


@login_required
def create_payment(request, agreement_pk):
    """Owner manually creates a payment."""
    if not request.user.is_owner():
        return HttpResponseForbidden('Only owners can create payments.')

    agreement = get_object_or_404(Agreement, pk=agreement_pk, owner=request.user)

    if request.method == 'POST':
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            payment           = form.save(commit=False)
            payment.agreement = agreement
            payment.tenant    = agreement.tenant
            payment.owner     = request.user
            payment.save()
            messages.success(request, 'Payment created successfully!')
            return redirect('payments:owner_payments')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = PaymentCreateForm(initial={'amount': agreement.rent_amount})

    return render(request, 'payments/payment_form.html', {
        'form': form, 'agreement': agreement
    })


@login_required
def auto_generate_payments(request, agreement_pk):
    """Owner auto-generates all monthly payments for an agreement."""
    if not request.user.is_owner():
        return HttpResponseForbidden('Only owners can generate payments.')

    agreement = get_object_or_404(Agreement, pk=agreement_pk, owner=request.user)

    if not agreement.is_active():
        messages.error(request, 'Payments can only be generated for active agreements.')
        return redirect('agreements:detail', pk=agreement_pk)

    if request.method == 'POST':
        # Install python-dateutil if not installed
        try:
            created = generate_monthly_payments(agreement)
            if created:
                messages.success(request, f'{created} monthly payment(s) generated successfully!')
            else:
                messages.info(request, 'All payments already exist for this agreement.')
        except Exception as e:
            messages.error(request, f'Error generating payments: {e}')
        return redirect('payments:owner_payments')

    return render(request, 'payments/auto_generate_confirm.html', {'agreement': agreement})


@login_required
def mark_paid(request, pk):
    """Owner marks a payment as paid."""
    payment = get_object_or_404(Payment, pk=pk, owner=request.user)

    if payment.is_paid():
        messages.warning(request, 'Payment is already marked as paid.')
        return redirect('payments:owner_payments')

    if request.method == 'POST':
        form = PaymentMarkPaidForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            payment            = form.save(commit=False)
            payment.status     = 'paid'
            if not payment.paid_date:
                payment.paid_date = timezone.now().date()
            payment.save()
            messages.success(request, 'Payment marked as paid!')
            return redirect('payments:owner_payments')
    else:
        form = PaymentMarkPaidForm(instance=payment, initial={'paid_date': timezone.now().date()})

    return render(request, 'payments/mark_paid_form.html', {
        'form': form, 'payment': payment
    })


@login_required
def cancel_payment(request, pk):
    """Owner cancels a payment."""
    payment = get_object_or_404(Payment, pk=pk, owner=request.user)
    if request.method == 'POST':
        payment.status = 'cancelled'
        payment.save()
        messages.success(request, 'Payment cancelled.')
        return redirect('payments:owner_payments')
    return render(request, 'payments/cancel_confirm.html', {'payment': payment})


# ── Tenant Views ──────────────────────────────────────────────────────────────

@login_required
def tenant_payments(request):
    """Tenant sees all their payments."""
    if not request.user.is_tenant():
        return redirect('dashboard:owner')

    payments = Payment.tenant_objects.filter(tenant=request.user).select_related(
        'owner', 'agreement'
    )
    # Update overdue
    for payment in payments:
        if payment.is_overdue():
            payment.status = 'overdue'
            payment.save()

    upcoming = payments.filter(status='pending').order_by('due_date').first()

    return render(request, 'payments/tenant_payments.html', {
        'payments': payments,
        'upcoming': upcoming,
    })


# ── Shared Views ──────────────────────────────────────────────────────────────

@login_required
def payment_detail(request, pk):
    """Owner or tenant views payment detail."""
    payment   = get_object_or_404(Payment, pk=pk)
    is_owner  = payment.owner  == request.user
    is_tenant = payment.tenant == request.user

    if not (is_owner or is_tenant):
        return HttpResponseForbidden('Access denied.')

    return render(request, 'payments/payment_detail.html', {
        'payment': payment, 'is_owner': is_owner, 'is_tenant': is_tenant
    })

@login_required
def delete_payment(request, pk):
    payment = get_object_or_404(Payment.all_objects, pk=pk, owner=request.user)

    if payment.status != 'cancelled':
        messages.error(request, 'Only cancelled payments can be removed.')
        return redirect('payments:owner_payments')

    if request.method == 'POST':
        payment.soft_delete_by_owner()
        messages.success(request, 'Payment removed from your list.')
        return redirect('payments:owner_payments')

    return render(request, 'base_delete_confirm.html', {
        'object': payment, 'type': 'Payment'
    })