from django.contrib import admin
from .models import Show, ShowEpisode, Tag, ShowReminder


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model"""
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    """Admin for Show model"""
    list_display = ['title', 'creator', 'is_recurring', 'recurrence_type', 'status', 'created_at']
    list_filter = ['status', 'is_recurring', 'recurrence_type', 'created_at']
    search_fields = ['title', 'description', 'creator__username']
    date_hierarchy = 'created_at'
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'thumbnail', 'creator', 'status', 'tags')
        }),
        ('External Links', {
            'fields': ('external_link', 'link_platform')
        }),
        ('Schedule', {
            'fields': ('is_recurring', 'recurrence_type', 'day_of_week', 'scheduled_time', 'cancelled_instances')
        }),
    )


@admin.register(ShowEpisode)
class ShowEpisodeAdmin(admin.ModelAdmin):
    """Admin for ShowEpisode model"""
    list_display = ['show', 'episode_number', 'title', 'air_date', 'created_at']
    list_filter = ['show', 'air_date']
    search_fields = ['title', 'description', 'show__title']
    date_hierarchy = 'air_date'


@admin.register(ShowReminder)
class ShowReminderAdmin(admin.ModelAdmin):
    """Admin for ShowReminder model"""
    list_display = ['show', 'scheduled_for', 'creator_response', 'reminder_sent_at', 'responded_at']
    list_filter = ['creator_response', 'scheduled_for']
    search_fields = ['show__title']
    date_hierarchy = 'scheduled_for'
    readonly_fields = ['created_at', 'reminder_sent_at']

