from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType


def get_content_types(request):
    """Return content type IDs for frontend reference"""
    show_ct = ContentType.objects.get(app_label='shows', model='show')
    news_ct = ContentType.objects.get(app_label='news', model='news')
    event_ct = ContentType.objects.get(app_label='events', model='event')
    
    return JsonResponse({
        'SHOW': show_ct.id,
        'NEWS': news_ct.id,
        'EVENT': event_ct.id,
        'debug': {
            'show': f"{show_ct.app_label} | {show_ct.model}",
            'news': f"{news_ct.app_label} | {news_ct.model}",
            'event': f"{event_ct.app_label} | {event_ct.model}",
        }
    })
