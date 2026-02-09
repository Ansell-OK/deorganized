# Generated manually to clean up Railway database
# Removes like_count and comment_count fields that were added by deleted migration 0009

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shows', '0008_show_share_count_alter_show_slug_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='show',
            name='comment_count',
        ),
        migrations.RemoveField(
            model_name='show',
            name='like_count',
        ),
    ]
