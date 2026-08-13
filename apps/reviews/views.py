from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Avg
from .models import Review
from .forms import ReviewForm
from apps.agreements.models import Agreement
from apps.properties.models import Property, Room


def get_star_display(rating):
    return "★" * rating + "☆" * (5 - rating)


# ── Tenant Reviews ────────────────────────────────────────────────────────────


@login_required
def write_review(request, agreement_pk, review_type):
    """Tenant writes review for property/room/owner. Owner writes review for tenant."""
    agreement = get_object_or_404(Agreement, pk=agreement_pk)

    # Validate access
    is_tenant = agreement.tenant == request.user
    is_owner = agreement.owner == request.user

    if not (is_tenant or is_owner):
        return HttpResponseForbidden("Access denied.")

    # Validate agreement status
    if agreement.status not in ["active", "terminated", "expired"]:
        messages.error(
            request, "You can only review after an agreement is active or completed."
        )
        return redirect("agreements:detail", pk=agreement_pk)

    # Validate review type permissions
    if is_tenant and review_type not in ["property", "room", "owner"]:
        return HttpResponseForbidden("Invalid review type.")
    if is_owner and review_type != "tenant":
        return HttpResponseForbidden("Owners can only review tenants.")

    # Check for duplicate review
    existing = Review.objects.filter(
        reviewer=request.user,
        agreement=agreement,
        review_type=review_type,
    ).first()
    if existing:
        messages.warning(request, "You have already submitted this review.")
        return redirect("reviews:my_reviews")

    # Determine target label
    if review_type == "property":
        target_name = agreement.property.title if agreement.property else "Property"
    elif review_type == "room":
        target_name = f"Room {agreement.room.room_number}" if agreement.room else "Room"
    elif review_type == "owner":
        target_name = agreement.owner.get_full_name() or agreement.owner.username
    else:
        target_name = agreement.tenant.get_full_name() or agreement.tenant.username

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.agreement = agreement
            review.review_type = review_type

            if review_type == "property":
                review.property = agreement.property
            elif review_type == "room":
                review.room = agreement.room
            elif review_type == "owner":
                review.reviewee = agreement.owner
                # review.property = agreement.property
                # review.room     = agreement.room
            elif review_type == "tenant":
                review.reviewee = agreement.tenant

            review.save()
            messages.success(request, "Review submitted successfully! Thank you.")
            return redirect("reviews:my_reviews")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ReviewForm()

    return render(
        request,
        "reviews/review_form.html",
        {
            "form": form,
            "agreement": agreement,
            "review_type": review_type,
            "target_name": target_name,
            "is_tenant": is_tenant,
            "is_owner": is_owner,
        },
    )


@login_required
def my_reviews(request):
    """User sees all reviews they have given."""
    reviews = Review.objects.filter(reviewer=request.user).select_related(
        "property", "room", "reviewee", "agreement"
    )
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})


@login_required
def reviews_received(request):
    """User sees all reviews they have received."""
    reviews = Review.objects.filter(reviewee=request.user).select_related(
        "reviewer", "agreement"
    )
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    return render(
        request,
        "reviews/reviews_received.html",
        {
            "reviews": reviews,
            "avg_rating": avg_rating,
        },
    )


def property_reviews(request, pk):
    """Public view — show all reviews for a property."""
    property = get_object_or_404(Property, pk=pk)
    reviews = Review.objects.filter(
        property=property, review_type="property"
    ).select_related("reviewer")
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    return render(
        request,
        "reviews/property_reviews.html",
        {
            "property": property,
            "reviews": reviews,
            "avg_rating": avg_rating,
        },
    )


def room_reviews(request, pk):
    """Public view — show all reviews for a room."""
    room = get_object_or_404(Room, pk=pk)
    reviews = Review.objects.filter(room=room, review_type="room").select_related(
        "reviewer"
    )
    avg_rating = reviews.aggregate(avg=Avg("rating"))["avg"]
    return render(
        request,
        "reviews/room_reviews.html",
        {
            "room": room,
            "reviews": reviews,
            "avg_rating": avg_rating,
        },
    )


@login_required
def delete_review(request, pk):
    """Reviewer deletes their own review."""
    review = get_object_or_404(Review, pk=pk, reviewer=request.user)
    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted.")
        return redirect("reviews:my_reviews")
    return render(request, "reviews/delete_confirm.html", {"review": review})
