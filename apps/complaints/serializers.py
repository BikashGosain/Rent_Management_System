from rest_framework import serializers
from django.utils import timezone
from .models import Complaint, ComplaintResponse


# ── Complaint Response ────────────────────────────────────────────────────────

class ComplaintResponseSerializer(serializers.ModelSerializer):
    responder_name = serializers.CharField(
        source='responder.get_full_name', read_only=True
    )
    responder_role = serializers.CharField(
        source='responder.role', read_only=True
    )

    class Meta:
        model  = ComplaintResponse
        fields = [
            'id', 'message', 'attachment',
            'responder_name', 'responder_role', 'created_at',
        ]
        read_only_fields = ['id', 'responder_name', 'responder_role', 'created_at']


# ── Complaint List ────────────────────────────────────────────────────────────

class ComplaintListSerializer(serializers.ModelSerializer):
    target_name   = serializers.SerializerMethodField()
    tenant_name   = serializers.CharField(source='tenant.get_full_name', read_only=True)
    owner_name    = serializers.CharField(source='owner.get_full_name',  read_only=True)
    response_count = serializers.IntegerField(source='responses.count',  read_only=True)

    class Meta:
        model  = Complaint
        fields = [
            'id', 'title', 'category', 'priority', 'status',
            'submitted_by', 'created_at', 'updated_at',
            'target_name', 'tenant_name', 'owner_name', 'response_count',
        ]

    def get_target_name(self, obj):
        return obj.get_target_name()


# ── Complaint Detail ──────────────────────────────────────────────────────────

class ComplaintDetailSerializer(serializers.ModelSerializer):
    target_name   = serializers.SerializerMethodField()
    tenant_name   = serializers.CharField(source='tenant.get_full_name', read_only=True)
    tenant_phone  = serializers.CharField(source='tenant.phone',         read_only=True)
    owner_name    = serializers.CharField(source='owner.get_full_name',  read_only=True)
    owner_phone   = serializers.CharField(source='owner.phone',          read_only=True)
    responses     = ComplaintResponseSerializer(many=True, read_only=True)

    class Meta:
        model  = Complaint
        fields = [
            'id', 'title', 'category', 'priority', 'status',
            'description', 'attachment', 'submitted_by',
            'created_at', 'updated_at', 'resolved_at',
            'property', 'room', 'agreement',
            'target_name', 'tenant_name', 'tenant_phone',
            'owner_name', 'owner_phone', 'responses',
        ]

    def get_target_name(self, obj):
        return obj.get_target_name()


# ── Submit Complaint ──────────────────────────────────────────────────────────

class SubmitComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Complaint
        fields = [
            'title', 'category', 'priority', 'description',
            'attachment', 'property', 'room', 'agreement',
        ]
        extra_kwargs = {
            'attachment': {'required': False},
            'property':   {'required': False},
            'room':       {'required': False},
            'agreement':  {'required': False},
            'priority':   {'required': False},
        }

    def validate(self, data):
        # Must have at least property or room
        if not data.get('property') and not data.get('room'):
            raise serializers.ValidationError(
                'Please select a property or room for the complaint.'
            )
        return data

    def create(self, validated_data):
        request      = self.context['request']
        submitted_by = self.context['submitted_by']  # 'tenant' or 'owner'

        # Get owner from room or property
        room     = validated_data.get('room')
        property = validated_data.get('property')

        if room:
            owner = room.property.owner
        elif property:
            owner = property.owner
        else:
            raise serializers.ValidationError('Could not determine owner.')

        return Complaint.objects.create(
            tenant=request.user,
            owner=owner,
            submitted_by=submitted_by,
            **validated_data,
        )


# ── Update Status ─────────────────────────────────────────────────────────────

class ComplaintStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Complaint
        fields = ['status']

    def validate_status(self, value):
        allowed = ['open', 'in_progress', 'resolved', 'closed']
        if value not in allowed:
            raise serializers.ValidationError(f'Status must be one of: {allowed}')
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        # Set resolved_at timestamp when resolved or closed
        if instance.status in ['resolved', 'closed']:
            instance.resolved_at = timezone.now()
        instance.save()
        return instance