from datetime import date
from dateutil.relativedelta import relativedelta
from .models import Payment


def generate_monthly_payments(agreement):
    """Auto-generate monthly rent payments for an agreement."""
    start = agreement.start_date
    end = agreement.end_date
    amount = agreement.rent_amount

    current = start
    created = 0

    while current <= end:
        # Skip if payment already exists for this month/year
        exists = Payment.objects.filter(
            agreement=agreement,
            payment_type="rent",
            month=current.month,
            year=current.year,
        ).exists()

        if not exists:
            due_date = date(current.year, current.month, 5)  # due on 5th of each month
            Payment.objects.create(
                agreement=agreement,
                tenant=agreement.tenant,
                owner=agreement.owner,
                payment_type="rent",
                amount=amount,
                due_date=due_date,
                month=current.month,
                year=current.year,
                status="pending",
                is_auto_generated=True,
            )
            created += 1

        current += relativedelta(months=1)

    return created
