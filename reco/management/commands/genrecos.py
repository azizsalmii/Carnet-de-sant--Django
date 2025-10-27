"""
Management command to generate recommendations for a user.

Computes features and applies rules to generate personalized recommendations.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from reco.services import compute_features_for_user, generate_recommendations_for_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate recommendations for a user based on their metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            required=True,
            help='Username to generate recommendations for'
        )

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        # Compute features
        self.stdout.write('Computing features...')
        features = compute_features_for_user(user.id)
        
        self.stdout.write(self.style.SUCCESS('Features computed:'))
        for key, value in features.items():
            self.stdout.write(f'  {key}: {value}')
        
        # Generate recommendations
        self.stdout.write('\nGenerating recommendations...')
        count = generate_recommendations_for_user(user.id, features)
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully generated {count} recommendations for {username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\nNo recommendations generated for {username}')
            )
