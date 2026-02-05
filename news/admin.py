from django.contrib import admin
from .models import News


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Admin for News model"""
    list_display = ['title', 'author', 'category', 'is_published', 'published_at', 'view_count', 'created_at']
    list_filter = ['is_published', 'category', 'published_at', 'created_at']
    search_fields = ['title', 'content', 'tags', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt', 'featured_image')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at')
        }),
        ('Metrics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
    )
