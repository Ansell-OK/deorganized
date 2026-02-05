from celery import shared_task
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Show, ShowReminder
from users.models import Notification


@shared_task
def check_upcoming_shows():
    """
    Checks for shows starting in 30 minutes and creates reminders.
    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()
    reminder_window_start = now + timedelta(minutes=25)  # 25-35 min window
    reminder_window_end = now + timedelta(minutes=35)
    
    # Find all recurring shows that are published
    recurring_shows = Show.objects.filter(
        is_recurring=True,
        status='published'
    ).select_related('creator')
    
    for show in recurring_shows:
        if not show.scheduled_time or not show.recurrence_type:
            continue
        
        # Check each date in the next hour
        for minutes_ahead in range(25, 36, 5):  # Check 25, 30, 35 min ahead
            check_datetime = now + timedelta(minutes=minutes_ahead)
            check_date = check_datetime.date()
            
            # Check if show should air on this date
            if show.should_air_on_date(check_date):
                # Construct the scheduled datetime
                scheduled_datetime = timezone.make_aware(
                    datetime.combine(check_date, show.scheduled_time)
                )
                
                # Only create reminder if it's 30 minutes ± 5 minutes from now
                time_until_show = (scheduled_datetime - now).total_seconds() / 60
                if 25 <= time_until_show <= 35:
                    # Create or get reminder
                    reminder, created = ShowReminder.objects.get_or_create(
                        show=show,
                        scheduled_for=scheduled_datetime,
                        defaults={'reminder_sent_at': now}
                    )
                    
                    if created:
                        # Create notification for the creator
                        Notification.objects.create(
                            recipient=show.creator,
                            actor=show.creator,  # Self-notification
                            notification_type='show_reminder',
                            content_type=None,
                            object_id=None
                        )
                        print(f"Created reminder for {show.title} at {scheduled_datetime}")


@shared_task
def auto_cancel_unconfirmed_shows():
    """
    Auto-cancels shows if creator hasn't responded within 30 minutes.
    Defaults to NO - show is cancelled.
    Runs every 5 minutes.
    """
    now = timezone.now()
    
    # Find pending reminders where show time has passed
    pending_reminders = ShowReminder.objects.filter(
        creator_response='PENDING',
        scheduled_for__lte=now
    ).select_related('show', 'show__creator')
    
    for reminder in pending_reminders:
        # Auto-cancel
        reminder.creator_response = 'CANCELLED'
        reminder.responded_at = now
        reminder.save()
        
        # Add to cancelled instances
        show = reminder.show
        date_str = reminder.scheduled_for.date().isoformat()
        
        if date_str not in show.cancelled_instances:
            show.cancelled_instances.append(date_str)
            show.save(update_fields=['cancelled_instances'])
        
        # Notify creator
        Notification.objects.create(
            recipient=show.creator,
            actor=show.creator,  # Self-notification
            notification_type='show_cancelled',
            content_type=None,
            object_id=None
        )
        print(f"Auto-cancelled show {show.title} for {reminder.scheduled_for}")


@shared_task
def cleanup_old_notifications():
    """
    Clean up old read notifications after 30 days.
    Runs daily.
    """
    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()[0]
    
    print(f"Cleaned up {deleted_count} old notifications")
    return deleted_count
