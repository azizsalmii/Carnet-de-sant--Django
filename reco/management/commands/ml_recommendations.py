"""
Management command to regenerate personalized recommendations using ML model.

Usage:
    python manage.py ml_recommendations --username <username>
    python manage.py ml_recommendations --all  # For all users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reco.services import compute_features_for_user, generate_recommendations_for_user
from reco.models import Recommendation

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate ML-powered personalized recommendations for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to generate recommendations for',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generate for all users',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing recommendations before generating',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        all_users = options.get('all')
        clear_existing = options.get('clear')

        if not username and not all_users:
            self.stderr.write(
                self.style.ERROR('Please specify --username <name> or --all')
            )
            return

        # Get users to process
        if all_users:
            users = User.objects.all()
            self.stdout.write(f'Processing {users.count()} users...')
        else:
            try:
                users = [User.objects.get(username=username)]
            except User.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f'User "{username}" does not exist')
                )
                return

        # Process each user
        total_created = 0
        total_cleared = 0

        for user in users:
            self.stdout.write(f'\n🔄 Processing user: {user.username}')

            # Clear existing if requested
            if clear_existing:
                deleted = Recommendation.objects.filter(user=user).delete()[0]
                total_cleared += deleted
                if deleted > 0:
                    self.stdout.write(f'   Cleared {deleted} existing recommendations')

            # Compute features
            features = compute_features_for_user(user.id)
            
            if not features or all(v == 0 for v in features.values()):
                self.stdout.write(
                    self.style.WARNING(
                        f'   ⚠️  No health data found for {user.username}. '
                        'Add metrics first.'
                    )
                )
                continue

            # Generate ML-powered recommendations
            count = generate_recommendations_for_user(user.id, features)
            total_created += count

            if count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'   ✓ Created {count} personalized recommendations'
                    )
                )
                
                # Show top recommendation
                top_reco = Recommendation.objects.filter(user=user).order_by('-score').first()
                if top_reco:
                    self.stdout.write(
                        f'   📌 Top: [{top_reco.category}] {top_reco.text[:60]}...'
                    )
                    self.stdout.write(
                        f'   💡 Confidence: {top_reco.score:.1%}'
                    )
                    if top_reco.rationale:
                        self.stdout.write(
                            f'   🎯 Why: {top_reco.rationale[:80]}...'
                        )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '   ⚠️  No recommendations generated (health metrics are good!)'
                    )
                )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Done! Created {total_created} personalized recommendations'
            )
        )
        if clear_existing:
            self.stdout.write(f'   Cleared {total_cleared} old recommendations')
        self.stdout.write('\n💡 View at: http://127.0.0.1:8000/api/recommendations/personalized/')
