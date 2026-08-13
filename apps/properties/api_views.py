from rest_framework import generics, permissions, filters
from .models import Property, Room
from .serializers import PropertySerializer, RoomSerializer
from .pagination import StandardPagination             

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user

class PropertyListCreateAPI(generics.ListCreateAPIView):
    serializer_class   = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class   = StandardPagination           
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['title', 'city', 'type']
    ordering_fields    = ['rent_price', 'created_at']

    def get_queryset(self):
        qs = Property.objects.prefetch_related('photos', 'rooms').all()
        city      = self.request.query_params.get('city')
        status    = self.request.query_params.get('status')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if city:      qs = qs.filter(city__icontains=city)
        if status:    qs = qs.filter(status=status)
        if min_price: qs = qs.filter(rent_price__gte=min_price)
        if max_price: qs = qs.filter(rent_price__lte=max_price)
        return qs

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class PropertyDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Property.objects.prefetch_related('photos', 'rooms')
    serializer_class   = PropertySerializer
    permission_classes = [IsOwnerOrReadOnly]
  

class RoomListCreateAPI(generics.ListCreateAPIView):
    serializer_class   = RoomSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class   = StandardPagination      

    def get_queryset(self):
        return Room.objects.filter(
            property_id=self.kwargs['property_id']
        ).select_related('facility').prefetch_related('photos')

    def perform_create(self, serializer):
        prop = Property.objects.get(pk=self.kwargs['property_id'])
        serializer.save(property=prop)

class RoomDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Room.objects.select_related('property').prefetch_related('facility', 'photos')
    serializer_class   = RoomSerializer
    permission_classes = [IsOwnerOrReadOnly]
