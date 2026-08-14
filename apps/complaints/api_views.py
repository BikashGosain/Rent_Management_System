# apps/complaints/api_views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Complaint
from .serializers import (
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    SubmitComplaintSerializer,
    ComplaintStatusSerializer,
    ComplaintResponseSerializer,
)
from apps.properties.pagination import StandardPagination


# ── Permissions ───────────────────────────────────────────────────────────────


class IsOwnerOrTenantOfComplaint(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.tenant == request.user or obj.owner == request.user


# ── Submit Complaint ──────────────────────────────────────────────────────────


class SubmitComplaintAPI(APIView):
    """
    POST /api/complaints/
    Tenant or owner submits a complaint.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Determine submitted_by from role
        if user.is_tenant():
            submitted_by = "tenant"
        elif user.is_owner():
            submitted_by = "owner"
        else:
            return Response(
                {"detail": "Only tenants or owners can submit complaints."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitComplaintSerializer(
            data=request.data,
            context={"request": request, "submitted_by": submitted_by},
        )
        if serializer.is_valid():
            complaint = serializer.save()
            return Response(
                {
                    "detail": "Complaint submitted successfully.",
                    "complaint_id": complaint.pk,
                    "status": complaint.status,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Tenant: My Complaints ─────────────────────────────────────────────────────


class MyComplaintsAPI(generics.ListAPIView):
    """
    GET /api/complaints/my/
    Tenant sees their submitted complaints.
    """

    serializer_class = ComplaintListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Complaint.objects.filter(tenant=self.request.user).select_related(
            "owner", "property", "room"
        )

        # Filters
        status_f = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        priority = self.request.query_params.get("priority")

        if status_f:
            qs = qs.filter(status=status_f)
        if category:
            qs = qs.filter(category=category)
        if priority:
            qs = qs.filter(priority=priority)

        return qs.order_by("-created_at")


# ── Owner: Received Complaints ────────────────────────────────────────────────


class OwnerComplaintsAPI(generics.ListAPIView):
    """
    GET /api/complaints/owner/
    Owner sees all complaints received for their properties.
    """

    serializer_class = ComplaintListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Complaint.objects.filter(owner=self.request.user).select_related(
            "tenant", "property", "room"
        )

        # Filters
        status_f = self.request.query_params.get("status")
        category = self.request.query_params.get("category")
        priority = self.request.query_params.get("priority")

        if status_f:
            qs = qs.filter(status=status_f)
        if category:
            qs = qs.filter(category=category)
        if priority:
            qs = qs.filter(priority=priority)

        return qs.order_by("-created_at")


# ── Complaint Detail ──────────────────────────────────────────────────────────


class ComplaintDetailAPI(generics.RetrieveAPIView):
    """
    GET /api/complaints/<pk>/
    Owner or tenant views full complaint detail with responses.
    """

    serializer_class = ComplaintDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTenantOfComplaint]

    def get_queryset(self):
        return Complaint.objects.select_related(
            "tenant", "owner", "property", "room", "agreement"
        ).prefetch_related("responses__responder")


# ── Owner: Update Status ──────────────────────────────────────────────────────


class UpdateComplaintStatusAPI(APIView):
    """
    PATCH /api/complaints/<pk>/status/
    Owner updates complaint status.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)

        # Only the owner of the complaint can update status
        if complaint.owner != request.user:
            return Response(
                {"detail": "Only the property owner can update complaint status."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ComplaintStatusSerializer(
            complaint, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "detail": "Status updated.",
                    "status": serializer.data["status"],
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Add Response to Complaint ─────────────────────────────────────────────────


class AddComplaintResponseAPI(APIView):
    """
    POST /api/complaints/<pk>/respond/
    Owner or tenant adds a response/message to a complaint thread.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)

        # Only owner or tenant involved can respond
        if complaint.owner != request.user and complaint.tenant != request.user:
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        # Cannot respond to closed complaint
        if complaint.status == "closed":
            return Response(
                {"detail": "Cannot respond to a closed complaint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ComplaintResponseSerializer(data=request.data)
        if serializer.is_valid():
            response = serializer.save(
                complaint=complaint,
                responder=request.user,
            )
            return Response(
                {
                    "detail": "Response added.",
                    "response_id": response.pk,
                    "data": ComplaintResponseSerializer(response).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Soft Delete Complaint ─────────────────────────────────────────────────────


class DeleteComplaintAPI(APIView):
    """
    DELETE /api/complaints/<pk>/delete/
    Owner or tenant soft-deletes a resolved/closed complaint.
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        complaint = get_object_or_404(Complaint, pk=pk)

        is_owner = complaint.owner == request.user
        is_tenant = complaint.tenant == request.user

        if not (is_owner or is_tenant):
            return Response(
                {"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN
            )

        if not complaint.is_resolved():
            return Response(
                {"detail": "Only resolved or closed complaints can be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if is_owner:
            complaint.soft_delete_by_owner()
        else:
            complaint.soft_delete_by_tenant()

        return Response({"detail": "Complaint removed."}, status=status.HTTP_200_OK)
