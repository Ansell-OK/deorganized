# Generated manually to clean up Railway database
# Uses raw SQL to drop columns that exist in database but not in Django's migration state

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shows', '0008_show_share_count_alter_show_slug_and_more'),
    ]

    operations = [
        # Use raw SQL to drop columns if they exist
        # This bypasses Django's migration state and works directly on the database
        migrations.RunSQL(
            sql="""
                ALTER TABLE shows_show 
                DROP COLUMN IF EXISTS like_count,
                DROP COLUMN IF EXISTS comment_count;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
