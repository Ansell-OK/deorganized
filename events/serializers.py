from rest_framework import serializers
from .models import Event
from django.contrib.auth import get_user_model

User = get_user_model()


class EventOrganizerSerializer(serializers.ModelSerializer):
    """Lightweight organizer info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture', 'is_verified']
        read_only_fields = fields


class EventSerializer(serializers.ModelSerializer):
    """Full event serializer"""
    organizer = EventOrganizerSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    status = serializers.CharField(source='status', read_only=True)
    is_upcoming = serializers.BooleanField(source='is_upcoming', read_only=True)
    is_ongoing = serializers.BooleanField(source='is_ongoing', read_only=True)
    is_past = serializers.BooleanField(source='is_past', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'banner_image',
            'organizer', 'start_datetime', 'end_datetime',
            'venue_name', 'address', 'is_virtual', 'meeting_link',
            'capacity', 'registration_link', 'registration_deadline',
            'is_public', 'created_at', 'updated_at',
            'like_count', 'comment_count',
            'status', 'is_upcoming', 'is_ongoing', 'is_past'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']
    
    def get_like_count(self, obj):
        """Get like count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_like_count', obj.like_count)
    
    def get_comment_count(self, obj):
        """Get comment count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_comment_count', obj.comment_count)
    
    def validate(self, data):
        """Validate event dates"""
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise serializers.ValidationError(
                    "End date/time must be after start date/time."
                )
        
        # Validate virtual event has meeting link
        if data.get('is_virtual') and not data.get('meeting_link'):
            raise serializers.ValidationError(
                "Virtual events must have a meeting link."
            )
        
        return data


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    organizer = EventOrganizerSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    
    def get_like_count(self, obj):
        """Get like count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_like_count', obj.like_count)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'banner_image', 'organizer',
            'start_datetime', 'end_datetime', 'venue_name',
            'is_virtual', 'is_public', 'status',
            'like_count'
        ]
        read_only_fields = fields


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating events"""
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'banner_image',
            'start_datetime', 'end_datetime',
            'venue_name', 'address', 'is_virtual', 'meeting_link',
            'capacity', 'registration_link', 'registration_deadline',
            'is_public'
        ]
    
    def validate(self, data):
        """Validate event dates"""
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        
        if start_datetime and end_datetime:
            if end_datetime <= start_datetime:
                raise serializers.ValidationError(
                    "End date/time must be after start date/time."
                )
        
        # Validate virtual event has meeting link
        if data.get('is_virtual') and not data.get('meeting_link'):
            raise serializers.ValidationError(
                "Virtual events must have a meeting link."
            )
        
        return data
