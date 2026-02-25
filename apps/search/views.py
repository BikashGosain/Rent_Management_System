from django.shortcuts import render
from apps.properties.models import Property, Room


def search_view(request):
    properties = Property.objects.filter(status='available').prefetch_related('photos', 'rooms')
    rooms      = Room.objects.filter(status='available').select_related('property', 'property__owner').prefetch_related('photos', 'facility')

    # ── Filters ──────────────────────────────────────────────────────────────
    city        = request.GET.get('city', '').strip()
    prop_type   = request.GET.get('type', '')
    rent_type   = request.GET.get('rent_type', '')
    min_price   = request.GET.get('min_price', '')
    max_price   = request.GET.get('max_price', '')
    bedrooms    = request.GET.get('bedrooms', '')
    furnishing  = request.GET.get('furnishing', '')
    location    = request.GET.get('location', '').strip()

    # Amenities
    has_wifi     = request.GET.get('wifi', '')
    has_ac       = request.GET.get('ac', '')
    has_parking  = request.GET.get('parking', '')
    has_laundry  = request.GET.get('laundry', '')
    has_lift     = request.GET.get('lift', '')
    has_cctv     = request.GET.get('cctv', '')

    # ── Filter Properties (whole) ─────────────────────────────────────────
    if city:
        properties = properties.filter(city__icontains=city)
    if location:
        properties = properties.filter(address__icontains=location) | properties.filter(landmark__icontains=location)
    if prop_type:
        properties = properties.filter(type=prop_type)
    if rent_type:
        properties = properties.filter(rent_type=rent_type)
    if furnishing:
        properties = properties.filter(furnishing=furnishing)
    if bedrooms:
        properties = properties.filter(total_bedrooms__gte=bedrooms)
    if min_price:
        properties = properties.filter(rent_price__gte=min_price)
    if max_price:
        properties = properties.filter(rent_price__lte=max_price)
    if has_wifi:
        properties = properties.filter(has_internet=True)
    if has_parking:
        properties = properties.filter(has_parking=True)

    # ── Filter Rooms ──────────────────────────────────────────────────────
    if city:
        rooms = rooms.filter(property__city__icontains=city)
    if location:
        rooms = rooms.filter(property__address__icontains=location) | rooms.filter(property__landmark__icontains=location)
    if prop_type:
        rooms = rooms.filter(property__type=prop_type)
    if furnishing:
        rooms = rooms.filter(furnishing=furnishing)
    if bedrooms:
        rooms = rooms.filter(bedrooms__gte=bedrooms)
    if min_price:
        rooms = rooms.filter(rent_price__gte=min_price)
    if max_price:
        rooms = rooms.filter(rent_price__lte=max_price)
    if has_wifi:
        rooms = rooms.filter(facility__wifi=True)
    if has_ac:
        rooms = rooms.filter(facility__ac=True)
    if has_parking:
        rooms = rooms.filter(facility__parking=True)
    if has_laundry:
        rooms = rooms.filter(facility__laundry=True)
    if has_lift:
        rooms = rooms.filter(facility__lift=True)
    if has_cctv:
        rooms = rooms.filter(facility__cctv=True)

    # Only show whole properties in results
    whole_properties = properties.filter(rent_type='whole')

    context = {
        'whole_properties': whole_properties,
        'rooms':            rooms,
        'total_results':    whole_properties.count() + rooms.count(),
        'filters': {
            'city':       city,
            'location':   location,
            'type':       prop_type,
            'rent_type':  rent_type,
            'min_price':  min_price,
            'max_price':  max_price,
            'bedrooms':   bedrooms,
            'furnishing': furnishing,
            'wifi':       has_wifi,
            'ac':         has_ac,
            'parking':    has_parking,
            'laundry':    has_laundry,
            'lift':       has_lift,
            'cctv':       has_cctv,
        },
        'property_types': Property.PROPERTY_TYPES,
        'furnishing_choices': Property.FURNISHING_CHOICES,
    }
    return render(request, 'search/results.html', context)