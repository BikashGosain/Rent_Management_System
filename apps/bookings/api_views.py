from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Booking
from .serializers import (
    BookingSerializer,
    BookPropertySerializer,
    BookRoomSerializer,
    OwnerResponseSerializer,
)
from apps.properties.models import Property, Room
from apps.notifications.utils import (
    notify_booking_received,
    notify_booking_accepted,
    notify_booking_rejected,
)
from apps.properties.pagination import StandardPagination


# ── Permissions ───────────────────────────────────────────────────────────────


class IsTenant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_tenant()


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_owner()


# ── Tenant: Book a whole property ─────────────────────────────────────────────


class BookPropertyAPI(APIView):
    """
    POST /api/bookings/property/<pk>/
    Tenant sends a booking request for a whole property.
    """

    permission_classes = [IsTenant]

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        serializer = BookPropertySerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            # Validate property manually (passed via URL not body)
            try:
                serializer.validate_property(prop)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            booking = serializer.save(tenant=request.user, property=prop)
            notify_booking_received(booking)
            return Response(
                {
                    "detail": "Booking request sent successfully.",
                    "booking_id": booking.pk,
                    "status": booking.status,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Tenant: Book a room ───────────────────────────────────────────────────────


class BookRoomAPI(APIView):
    """
    POST /api/bookings/room/<room_pk>/
    Tenant sends a booking request for a room.
    """

    permission_classes = [IsTenant]

    def post(self, request, room_pk):
        room = get_object_or_404(Room, pk=room_pk)
        serializer = BookRoomSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.validate_room(room)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            booking = serializer.save(tenant=request.user, room=room)
            notify_booking_received(booking)
            return Response(
                {
                    "detail": "Booking request sent successfully.",
                    "booking_id": booking.pk,
                    "status": booking.status,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Tenant: My bookings ───────────────────────────────────────────────────────


class MyBookingsAPI(generics.ListAPIView):
    """
    GET /api/bookings/my/
    Tenant sees their own bookings.
    """

    serializer_class = BookingSerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Booking.tenant_objects.filter(tenant=self.request.user).select_related(
            "property", "room", "room__property"
        )

        # Filter by status
        status_f = self.request.query_params.get("status")
        if status_f:
            qs = qs.filter(status=status_f)

        return qs.order_by("-created_at")


# ── Tenant: Cancel booking ────────────────────────────────────────────────────


class CancelBookingAPI(APIView):
    """
    POST /api/bookings/<pk>/cancel/
    Tenant cancels their pending booking.
    """

    permission_classes = [IsTenant]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, tenant=request.user)

        if not booking.is_pending():
            return Response(
                {"detail": "Only pending bookings can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "cancelled"
        booking.cancelled_by = "tenant"
        booking.save()

        return Response(
            {"detail": "Booking cancelled successfully."}, status=status.HTTP_200_OK
        )


# ── Owner: All booking requests ───────────────────────────────────────────────


class OwnerBookingsAPI(generics.ListAPIView):
    """
    GET /api/bookings/owner/
    Owner sees all booking requests for their properties/rooms.
    """

    serializer_class = BookingSerializer
    permission_classes = [IsOwner]
    pagination_class = StandardPagination

    def get_queryset(self):
        user = self.request.user
        qs = Booking.owner_objects.filter(property__owner=user).select_related(
            "tenant", "property", "room", "room__property"
        ) | Booking.owner_objects.filter(room__property__owner=user).select_related(
            "tenant", "property", "room", "room__property"
        )

        # Filter by status
        status_f = self.request.query_params.get("status")
        if status_f:
            qs = qs.filter(status=status_f)

        return qs.order_by("-created_at")


# ── Booking Detail ────────────────────────────────────────────────────────────


class BookingDetailAPI(generics.RetrieveAPIView):
    """
    GET /api/bookings/<pk>/
    Owner or tenant views booking detail.
    """

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        booking = get_object_or_404(Booking.all_objects, pk=self.kwargs["pk"])
        user = self.request.user

        is_owner = booking.get_owner() == user
        is_tenant = booking.tenant == user

        if not (is_owner or is_tenant):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You do not have access to this booking.")

        return booking


# ── Owner: Accept booking ─────────────────────────────────────────────────────


class AcceptBookingAPI(APIView):
    """
    POST /api/bookings/<pk>/accept/
    Owner accepts a pending booking.
    """

    permission_classes = [IsOwner]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if booking.get_owner() != request.user:
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        if not booking.is_pending():
            return Response(
                {"detail": "Only pending bookings can be accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OwnerResponseSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            booking = serializer.save()
            booking.status = "accepted"
            booking.save()
            notify_booking_accepted(booking)

            # Mark room/property as occupied
            if booking.room:
                booking.room.status = "occupied"
                booking.room.save()
            elif booking.property:
                booking.property.status = "occupied"
                booking.property.save()

            return Response(
                {
                    "detail": "Booking accepted.",
                    "booking": BookingSerializer(booking).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Owner: Reject booking ─────────────────────────────────────────────────────


class RejectBookingAPI(APIView):
    """
    POST /api/bookings/<pk>/reject/
    Owner rejects a pending booking.
    """

    permission_classes = [IsOwner]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if booking.get_owner() != request.user:
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        if not booking.is_pending():
            return Response(
                {"detail": "Only pending bookings can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OwnerResponseSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            booking = serializer.save()
            booking.status = "rejected"
            booking.cancelled_by = "owner"
            booking.save()
            notify_booking_rejected(booking)

            return Response(
                {
                    "detail": "Booking rejected.",
                    "booking": BookingSerializer(booking).data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Owner: Cancel accepted booking ────────────────────────────────────────────


class OwnerCancelBookingAPI(APIView):
    """
    POST /api/bookings/<pk>/owner-cancel/
    Owner cancels an accepted booking and marks room/property available again.
    """

    permission_classes = [IsOwner]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk)

        if booking.get_owner() != request.user:
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        booking.status = "cancelled"
        booking.cancelled_by = "owner"
        booking.save()

        # Mark back to available
        if booking.room:
            booking.room.status = "available"
            booking.room.save()
        elif booking.property:
            booking.property.status = "available"
            booking.property.save()

        return Response({"detail": "Booking cancelled."}, status=status.HTTP_200_OK)


# ── Delete booking (soft delete) ──────────────────────────────────────────────


class DeleteBookingAPI(APIView):
    """
    DELETE /api/bookings/<pk>/delete/
    Owner or tenant soft-deletes a cancelled/rejected booking.
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        booking = get_object_or_404(Booking.all_objects, pk=pk)

        is_owner = booking.get_owner() == request.user
        is_tenant = booking.tenant == request.user

        if not (is_owner or is_tenant):
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        if booking.status not in ["cancelled", "rejected"]:
            return Response(
                {
                    "detail": f"Cannot delete a booking with status: {booking.get_status_display()}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_owner:
            booking.soft_delete_by_owner()
        else:
            booking.soft_delete_by_tenant()

        return Response({"detail": "Booking removed."}, status=status.HTTP_200_OK)
