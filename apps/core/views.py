from django.shortcuts import render
from django.db.models import Avg, Count
from apps.properties.models import Property
from apps.accounts.models import User
from apps.reviews.models import Review


def home(request):
    # Stats
    total_properties = Property.objects.filter(status='available').count()
    total_owners     = User.objects.filter(role='owner').count()
    total_tenants    = User.objects.filter(role='tenant').count()

    # Featured properties (latest 6 available)
    featured_whole = Property.objects.filter(
        status='available', rent_type='whole'
    ).prefetch_related('photos').order_by('-created_at')[:3]

    featured_rooms = Property.objects.filter(
        status='available', rent_type='rooms'
    ).prefetch_related('photos', 'rooms').order_by('-created_at')[:3]

    # Latest reviews with ratings
    testimonials = Review.objects.filter(
        review_type='property'
    ).select_related('reviewer', 'property').order_by('-created_at')[:6]

    return render(request, 'core/home.html', {
        'total_properties': total_properties,
        'total_owners':     total_owners,
        'total_tenants':    total_tenants,
        'featured_whole':   featured_whole,
        'featured_rooms':   featured_rooms,
        'testimonials':     testimonials,
    })