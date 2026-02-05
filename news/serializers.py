from rest_framework import serializers
from .models import News
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class NewsAuthorSerializer(serializers.ModelSerializer):
    """Lightweight author info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture', 'is_verified']
        read_only_fields = fields


class NewsSerializer(serializers.ModelSerializer):
    """Full news article serializer"""
    author = NewsAuthorSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'featured_image',
            'author', 'category', 'tags', 'tags_list',
            'is_published', 'published_at', 'view_count',
            'created_at', 'updated_at',
            'like_count', 'comment_count'
        ]
        read_only_fields = ['slug', 'author', 'created_at', 'updated_at', 'view_count']
    
    def get_like_count(self, obj):
        """Get like count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_like_count', obj.like_count)
    
    def get_comment_count(self, obj):
        """Get comment count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_comment_count', obj.comment_count)
    
    def create(self, validated_data):
        """Auto-set published_at if is_published is True"""
        if validated_data.get('is_published') and not validated_data.get('published_at'):
            validated_data['published_at'] = timezone.now()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Auto-set published_at when transitioning to published"""
        if validated_data.get('is_published') and not instance.is_published:
            if not validated_data.get('published_at'):
                validated_data['published_at'] = timezone.now()
        return super().update(instance, validated_data)


class NewsListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    author = NewsAuthorSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    
    def get_like_count(self, obj):
        """Get like count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_like_count', obj.like_count)
    
    def get_comment_count(self, obj):
        """Get comment count from annotation or property"""
        # Use the renamed annotation to avoid conflict with model property
        return getattr(obj, '_comment_count', obj.comment_count)
    
    class Meta:
        model = News
        fields = [
            'id', 'title', 'slug', 'excerpt', 'featured_image',
            'author', 'category', 'is_published', 'published_at',
            'view_count', 'like_count', 'comment_count'
        ]
        read_only_fields = fields


class NewsCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating news articles"""
    class Meta:
        model = News
        fields = [
            'title', 'content', 'excerpt', 'featured_image',
            'category', 'tags', 'is_published'
        ]
