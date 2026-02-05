from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.text import slugify


class News(models.Model):
    """
    Model representing news articles with featured images and engagement features.
    """
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('announcement', 'Announcement'),
        ('update', 'Update'),
        ('feature', 'Feature'),
        ('review', 'Review'),
        ('interview', 'Interview'),
    ]
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short summary for previews"
    )
    featured_image = models.ImageField(
        upload_to='news/featured/',
        blank=True,
        null=True
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_articles'
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated tags"
    )
    
    # Publishing
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    
    # Engagement metrics
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Generic relations for likes and comments
    likes = GenericRelation('users.Like', related_query_name='news')
    comments = GenericRelation('users.Comment', related_query_name='news')
    
    class Meta:
        verbose_name_plural = 'News'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['is_published', '-published_at']),
            models.Index(fields=['author', '-published_at']),
            models.Index(fields=['category', '-published_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def like_count(self):
        return self.likes.count()
    
    @property
    def comment_count(self):
        return self.comments.count()
    
    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
