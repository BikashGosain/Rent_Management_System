from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Property, Room
from .pagination import StandardPagination
from .serializers import (
    PropertyListSerializer,
    PropertyDetailSerializer,
    RoomListSerializer,
    RoomDetailSerializer,
    RoomWriteSerializer,
    RoomFacilitySerializer,
)


# ── Permissions ───────────────────────────────────────────────────────────────


class IsOwnerOfProperty(permissions.BasePermission):
    """Only the property owner can write. Anyone can read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # obj is Room — check its property owner
        if hasattr(obj, "property"):
            return obj.property.owner == request.user
        # obj is Property
        return obj.owner == request.user


# ── Property APIs ─────────────────────────────────────────────────────────────


class PropertyListCreateAPI(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "city", "state", "type"]
    ordering_fields = ["rent_price", "created_at"]

    def get_serializer_class(self):
        return PropertyListSerializer

    def get_queryset(self):
        qs = (
            Property.objects.select_related("owner")
            .prefetch_related("photos", "rooms")
            .all()
        )

        city = self.request.query_params.get("city")
        status_p = self.request.query_params.get("status")
        rent_type = self.request.query_params.get("rent_type")
        prop_type = self.request.query_params.get("type")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if city:
            qs = qs.filter(city__icontains=city)
        if status_p:
            qs = qs.filter(status=status_p)
        if rent_type:
            qs = qs.filter(rent_type=rent_type)
        if prop_type:
            qs = qs.filter(type=prop_type)
        if min_price:
            qs = qs.filter(rent_price__gte=min_price)
        if max_price:
            qs = qs.filter(rent_price__lte=max_price)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PropertyDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfProperty]
    serializer_class = PropertyDetailSerializer
    queryset = Property.objects.select_related("owner").prefetch_related(
        "photos", "rooms__photos", "rooms__facility"
    )


# ── Room APIs ─────────────────────────────────────────────────────────────────


class RoomListCreateAPI(generics.ListCreateAPIView):
    """
    GET  /api/properties/<property_id>/rooms/  → list rooms of a property
    POST /api/properties/<property_id>/rooms/  → owner adds a room
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RoomWriteSerializer
        return RoomListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["property_id"] = self.kwargs.get("property_id")
        return ctx

    def get_queryset(self):
        qs = (
            Room.objects.filter(property_id=self.kwargs["property_id"])
            .select_related("property__owner")
            .prefetch_related("photos", "facility")
        )

        # Filter by status
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)

        # Filter by room_type
        room_type = self.request.query_params.get("room_type")
        if room_type:
            qs = qs.filter(room_type=room_type)

        # Filter by price
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            qs = qs.filter(rent_price__gte=min_price)
        if max_price:
            qs = qs.filter(rent_price__lte=max_price)

        return qs

    def perform_create(self, serializer):
        prop = get_object_or_404(Property, pk=self.kwargs["property_id"])
        # Only owner can add rooms
        if prop.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only the property owner can add rooms.")
        serializer.save(property=prop)


class RoomDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/rooms/<id>/  → full room detail
    PUT    /api/rooms/<id>/  → owner edits
    DELETE /api/rooms/<id>/  → owner deletes
    """

    permission_classes = [IsOwnerOfProperty]
    queryset = Room.objects.select_related("property__owner").prefetch_related(
        "photos", "facility"
    )

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return RoomWriteSerializer
        return RoomDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.get_object():
            ctx["property_id"] = self.get_object().property_id
        return ctx


class RoomFacilityAPI(APIView):
    """
    GET  /api/rooms/<room_id>/facility/  → view facilities
    POST /api/rooms/<room_id>/facility/  → create or update facilities
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_room(self, room_id):
        return get_object_or_404(
            Room.objects.select_related("property__owner"), pk=room_id
        )

    def get(self, request, room_id):
        room = self.get_room(room_id)
        facility = getattr(room, "facility", None)
        if not facility:
            return Response(
                {"detail": "No facilities added yet."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(RoomFacilitySerializer(facility).data)

    def post(self, request, room_id):
        room = self.get_room(room_id)

        # Only owner can set facilities
        if room.property.owner != request.user:
            return Response(
                {"detail": "Only the property owner can update facilities."},
                status=status.HTTP_403_FORBIDDEN,
            )

        facility = getattr(room, "facility", None)

        if facility:
            # Update existing
            serializer = RoomFacilitySerializer(
                facility, data=request.data, partial=True
            )
        else:
            # Create new
            serializer = RoomFacilitySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(room=room)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Global Room Search API ────────────────────────────────────────────────────


class RoomSearchAPI(generics.ListAPIView):
    """
    GET /api/rooms/search/
    Params: city, status, room_type, min_price, max_price, furnishing
    """

    serializer_class = RoomListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["room_number", "property__city", "property__title"]
    ordering_fields = ["rent_price", "floor_number", "created_at"]

    def get_queryset(self):
        qs = (
            Room.objects.select_related("property__owner")
            .prefetch_related("photos", "facility")
            .all()
        )

        city = self.request.query_params.get("city")
        status = self.request.query_params.get("status")
        room_type = self.request.query_params.get("room_type")
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        furnishing = self.request.query_params.get("furnishing")
        wifi = self.request.query_params.get("wifi")

        if city:
            qs = qs.filter(property__city__icontains=city)
        if status:
            qs = qs.filter(status=status)
        if room_type:
            qs = qs.filter(room_type=room_type)
        if min_price:
            qs = qs.filter(rent_price__gte=min_price)
        if max_price:
            qs = qs.filter(rent_price__lte=max_price)
        if furnishing:
            qs = qs.filter(furnishing=furnishing)
        if wifi == "true":
            qs = qs.filter(facility__wifi=True)

        return qs
