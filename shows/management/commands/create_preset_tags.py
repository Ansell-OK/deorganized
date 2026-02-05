"""
Management command to create preset tags for shows
"""
from django.core.management.base import BaseCommand
from shows.models import Tag


class Command(BaseCommand):
    help = 'Create preset tags for streaming categories'

    def handle(self, *args, **options):
        preset_tags = [
            # Crypto & Blockchain
            'Bitcoin',
            'Crypto',
            'Blockchain',
            'Stacks',
            'DeFi',
            'NFTs',
            'Web3',
            
            # Gaming
            'Gaming',
            'Esports',
            'Retro Gaming',
            'Indie Games',
            
            # Tech
            'Technology',
            'Programming',
            'Software Development',
            'AI & Machine Learning',
            'Cybersecurity',
            
            # Business & Finance
            'Business',
            'Finance',
            'Investing',
            'Trading',
            'Entrepreneurship',
            
            # Lifestyle & Entertainment
            'Music',
            'Art',
            'Comedy',
            'Talk Show',
            'News',
            'Politics',
            'Sports',
            'Fitness',
            'Cooking',
            'Travel',
            
            # Education
            'Education',
            'Tutorial',
            'Science',
            'History',
            
            # Creative
            'Creative',
            'Design',
            'Photography',
            'Video Editing',
        ]

        created_count = 0
        existing_count = 0

        for tag_name in preset_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name.lower().replace(' ', '-').replace('&', 'and')}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created tag: {tag_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- Tag already exists: {tag_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Complete! Created {created_count} new tags, {existing_count} already existed.'
            )
        )
