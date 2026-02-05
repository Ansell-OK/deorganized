from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone


class Event(models.Model):
    """
    Model representing events with scheduling, location, and registration support.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    banner_image = models.ImageField(
        upload_to='events/banners/',
        blank=True,
        null=True
    )
    
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_events'
    )
    
    # Scheduling
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
    # Location
    venue_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, help_text="Link for virtual events")
    
    # Registration
    capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum number of attendees (leave blank for unlimited)"
    )
    registration_link = models.URLField(blank=True)
    registration_deadline = models.DateTimeField(blank=True, null=True)
    
    # Privacy
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Generic relations for likes and comments
    likes = GenericRelation('users.Like', related_query_name='event')
    comments = GenericRelation('users.Comment', related_query_name='event')
    
    class Meta:
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'is_public']),
            models.Index(fields=['organizer', '-start_datetime']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_datetime.strftime('%Y-%m-%d')}"
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()
    
    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.start_datetime > timezone.now()
    
    @property
    def is_ongoing(self):
        """Check if event is currently happening"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime
    
    @property
    def is_past(self):
        """Check if event has ended"""
        return self.end_datetime < timezone.now()
    
    @property
    def status(self):
        """Return current event status"""
        if self.is_ongoing:
            return "ongoing"
        elif self.is_upcoming:
            return "upcoming"
        else:
            return "past"
