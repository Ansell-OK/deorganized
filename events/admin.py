from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for Event model"""
    list_display = ['title', 'organizer', 'start_datetime', 'end_datetime', 'is_virtual', 'is_public', 'created_at']
    list_filter = ['is_virtual', 'is_public', 'start_datetime', 'created_at']
    search_fields = ['title', 'description', 'venue_name', 'organizer__username']
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'banner_image', 'organizer')
        }),
        ('Scheduling', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Location', {
            'fields': ('is_virtual', 'venue_name', 'address', 'meeting_link')
        }),
        ('Registration', {
            'fields': ('capacity', 'registration_link', 'registration_deadline')
        }),
        ('Settings', {
            'fields': ('is_public',)
        }),
    )
