# apps/search/api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from apps.properties.models import Property, Room
from apps.properties.pagination import StandardPagination
from .serializers import SearchPropertySerializer, SearchRoomSerializer


class SearchAPI(APIView):
    """
    GET /api/search/
    Searches both properties and rooms with same filters as your search_view.

    Params:
        city, location, type, rent_type, min_price, max_price,
        bedrooms, furnishing,
        wifi, ac, parking, laundry, lift, cctv
        result_type = all | properties | rooms   (default: all)
        page, page_size
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # ── Read all filter params (mirrors your search_view exactly) ──────
        city = request.query_params.get("city", "").strip()
        location = request.query_params.get("location", "").strip()
        prop_type = request.query_params.get("type", "")
        rent_type = request.query_params.get("rent_type", "")
        min_price = request.query_params.get("min_price", "")
        max_price = request.query_params.get("max_price", "")
        bedrooms = request.query_params.get("bedrooms", "")
        furnishing = request.query_params.get("furnishing", "")

        # Amenities
        has_wifi = request.query_params.get("wifi", "")
        has_ac = request.query_params.get("ac", "")
        has_parking = request.query_params.get("parking", "")
        has_laundry = request.query_params.get("laundry", "")
        has_lift = request.query_params.get("lift", "")
        has_cctv = request.query_params.get("cctv", "")

        # What to return
        result_type = request.query_params.get(
            "result_type", "all"
        )  # all | properties | rooms

        # ── Filter Properties (mirrors your search_view) ───────────────────
        properties = (
            Property.objects.filter(status="available")
            .select_related("owner")
            .prefetch_related("photos", "rooms")
        )

        if city:
            properties = properties.filter(city__icontains=city)
        if location:
            properties = properties.filter(
                address__icontains=location
            ) | properties.filter(landmark__icontains=location)
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

        whole_properties = properties.filter(rent_type="whole")
        room_properties = properties.filter(rent_type="rooms")

        # ── Filter Rooms (mirrors your search_view) ────────────────────────
        rooms = (
            Room.objects.filter(status="available")
            .select_related("property", "property__owner")
            .prefetch_related("photos", "facility")
        )

        if city:
            rooms = rooms.filter(property__city__icontains=city)
        if location:
            rooms = rooms.filter(property__address__icontains=location) | rooms.filter(
                property__landmark__icontains=location
            )
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

        # ── Paginate and Serialize ─────────────────────────────────────────
        paginator = StandardPagination()
        ctx = {"request": request}

        # Build response based on result_type
        response_data = {
            "total_results": 0,
            "filters_applied": self._active_filters(request),
        }

        if result_type in ["all", "properties"]:
            # Whole properties
            whole_page = paginator.paginate_queryset(whole_properties, request)
            whole_data = SearchPropertySerializer(
                whole_page, many=True, context=ctx
            ).data

            # Room-type properties
            room_prop_page = paginator.paginate_queryset(room_properties, request)
            room_prop_data = SearchPropertySerializer(
                room_prop_page, many=True, context=ctx
            ).data

            response_data["whole_properties"] = {
                "count": whole_properties.count(),
                "results": whole_data,
            }
            response_data["room_properties"] = {
                "count": room_properties.count(),
                "results": room_prop_data,
            }

        if result_type in ["all", "rooms"]:
            rooms_page = paginator.paginate_queryset(rooms, request)
            rooms_data = SearchRoomSerializer(rooms_page, many=True, context=ctx).data

            response_data["rooms"] = {
                "count": rooms.count(),
                "results": rooms_data,
            }

        # Total
        total = 0
        if result_type in ["all", "properties"]:
            total += whole_properties.count() + room_properties.count()
        if result_type in ["all", "rooms"]:
            total += rooms.count()
        response_data["total_results"] = total

        return Response(response_data)

    def _active_filters(self, request):
        """Return only the filters that were actually used."""
