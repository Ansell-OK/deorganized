"""
Django signals for creating notifications on user interactions.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Like, Comment, Notification


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    """
    Create notification when someone likes content.
    Only creates notification if:
    1. This is a new like (created=True)
    2. The content object has a 'creator' attribute
    3. The liker is not the creator (don't notify self-likes)
    """
    if not created:
        return
    
    # Check if content object has a creator
    content_object = instance.content_object
    if not hasattr(content_object, 'creator'):
        return
    
    # Don't notify if user likes their own content
    if instance.user == content_object.creator:
        return
    
    Notification.objects.create(
        recipient=content_object.creator,
        actor=instance.user,
        notification_type='like',
        content_type=instance.content_type,
        object_id=instance.object_id
    )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """
    Create notification when someone comments on content.
    Only creates notification if:
    1. This is a new comment (created=True)
    2. The content object has a 'creator' attribute
    3. The commenter is not the creator (don't notify self-comments)
    4. This is a top-level comment (not a reply)
    
    Note: Reply notifications would need separate logic to notify parent comment author
    """
    if not created:
        return
    
    # Check if content object has a creator
    content_object = instance.content_object
    if not hasattr(content_object, 'creator'):
        return
    
    # Don't notify if user comments on their own content
    if instance.user == content_object.creator:
        return
    
    # Only notify on top-level comments (not replies)
    # For replies, you might want to notify the parent comment author instead
    if instance.parent is not None:
        return
    
    Notification.objects.create(
        recipient=content_object.creator,
        actor=instance.user,
        notification_type='comment',
        content_type=instance.content_type,
        object_id=instance.object_id
    )
