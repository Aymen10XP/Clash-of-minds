import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from quiz.models import Question, Topic


DEFAULT_PLAYER_PASSWORD = 'PlayerDemo!2026'
DEFAULT_ADMIN_PASSWORD = 'AdminDemo!2026'


class Command(BaseCommand):
    help = 'Seed a complete local demo with a player, an admin, topics, questions, and answers.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--player-password',
            default=os.environ.get('DEMO_PLAYER_PASSWORD', DEFAULT_PLAYER_PASSWORD),
            help='Password for demo_player (or set DEMO_PLAYER_PASSWORD).',
        )
        parser.add_argument(
            '--admin-password',
            default=os.environ.get('DEMO_ADMIN_PASSWORD', DEFAULT_ADMIN_PASSWORD),
            help='Password for demo_admin (or set DEMO_ADMIN_PASSWORD).',
        )
        parser.add_argument(
            '--allow-production',
            action='store_true',
            help='Explicitly allow demo accounts to be created while DEBUG is disabled.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options['allow_production']:
            raise CommandError(
                'Demo data is disabled when DEBUG=False. Use --allow-production only if intentional.'
            )

        call_command('seed_quiz', verbosity=options['verbosity'])

        user_model = get_user_model()
        player, player_created = user_model.objects.get_or_create(
            username='demo_player',
            defaults={'email': 'player@clashofminds.local', 'country': 'TN'},
        )
        player.email = 'player@clashofminds.local'
        player.country = 'TN'
        player.is_active = True
        player.is_staff = False
        player.is_superuser = False
        player.set_password(options['player_password'])
        player.save()

        admin, admin_created = user_model.objects.get_or_create(
            username='demo_admin',
            defaults={'email': 'admin@clashofminds.local', 'country': 'TN'},
        )
        admin.email = 'admin@clashofminds.local'
        admin.country = 'TN'
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = False
        admin.set_password(options['admin_password'])
        admin.save()

        shared_topics = list(Topic.objects.filter(is_active=True).order_by('sort_order', 'title')[:4])
        player.favorite_topics.set(shared_topics)
        admin.favorite_topics.set(shared_topics)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Demo database is ready.'))
        self.stdout.write(
            f"  Player: demo_player / {options['player_password']} "
            f"({'created' if player_created else 'updated'})"
        )
        self.stdout.write(
            f"  Admin:  demo_admin / {options['admin_password']} "
            f"({'created' if admin_created else 'updated'})"
        )
        self.stdout.write(
            f'  Quiz:   {Topic.objects.count()} topics, '
            f'{Question.objects.filter(is_active=True).count()} active questions'
        )
        self.stdout.write('  Admin console: /admin-console')
