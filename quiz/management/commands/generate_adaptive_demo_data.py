"""Create explicitly labeled synthetic responses for an adaptive-model demo."""

import math
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from quiz.models import Question, TopScoreResponse, TopScoreRun


class Command(BaseCommand):
    help = 'Replace the synthetic adaptive demo cohort with generated practice responses.'

    def add_arguments(self, parser):
        parser.add_argument('--players', type=int, default=80)
        parser.add_argument('--runs-per-player', type=int, default=2)
        parser.add_argument('--questions-per-run', type=int, default=10)
        parser.add_argument('--seed', type=int, default=25010)

    @transaction.atomic
    def handle(self, *args, **options):
        player_count = options['players']
        runs_per_player = options['runs_per_player']
        questions_per_run = options['questions_per_run']
        if player_count < 8:
            raise CommandError('--players must be at least 8 for the documented training split.')
        if runs_per_player < 1 or questions_per_run < 1:
            raise CommandError('Run and question counts must be positive.')

        questions = list(
            Question.objects.filter(is_active=True, topic__is_active=True)
            .prefetch_related('choices', 'topic')
            .order_by('pk')
        )
        if len(questions) < questions_per_run:
            raise CommandError(
                f'Found {len(questions)} active questions; need at least '
                f'{questions_per_run}. Run "manage.py seed_quiz" first.'
            )

        rng = random.Random(options['seed'])
        user_model = get_user_model()
        TopScoreRun.objects.filter(
            selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
        ).delete()
        created_responses = 0
        created_runs = 0

        players = []
        for player_index in range(1, player_count + 1):
            username = f'adaptive_synthetic_{player_index:03d}'
            user, _ = user_model.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.invalid',
                    'country': 'TN',
                    'is_active': False,
                },
            )
            user.is_active = False
            user.set_unusable_password()
            user.save(update_fields=('is_active', 'password'))
            players.append((user, rng.uniform(0.18, 0.9)))

        topic_aptitudes = {}
        for user, aptitude in players:
            topic_aptitudes[user.pk] = {
                question.topic_id: rng.uniform(-0.55, 0.55)
                for question in questions
            }

        difficulty_log_odds = {'easy': 1.25, 'medium': 0.35, 'hard': -0.4}
        for user, aptitude in players:
            for _ in range(runs_per_player):
                run = TopScoreRun.objects.create(
                    user=user,
                    selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
                )
                chosen_questions = rng.sample(questions, questions_per_run)
                responses = []
                score = 0
                end_reason = TopScoreRun.EndReason.QUIT

                for sequence, question in enumerate(chosen_questions, start=1):
                    choices = list(question.choices.all())
                    correct_choice = next(
                        (choice for choice in choices if choice.is_correct), None,
                    )
                    wrong_choices = [choice for choice in choices if not choice.is_correct]
                    if correct_choice is None or len(wrong_choices) != 3:
                        raise CommandError(
                            f'Question {question.pk} must have four choices and one correct answer.'
                        )

                    log_odds = (
                        difficulty_log_odds.get(question.difficulty, 0.35)
                        + (aptitude - 0.55) * 2.5
                        + topic_aptitudes[user.pk][question.topic_id]
                    )
                    success_probability = 1 / (1 + math.exp(-log_odds))
                    correct = rng.random() < success_probability
                    selected_choice = (
                        correct_choice if correct else rng.choice(wrong_choices)
                    )

                    difficulty_time = {'easy': 2_800, 'medium': 4_600, 'hard': 6_300}
                    response_time = int(
                        difficulty_time.get(question.difficulty, 4_600)
                        + (0.55 - aptitude) * 2_400
                        + (0 if correct else 500)
                        + rng.gauss(0, 700)
                    )
                    response_time = min(max(response_time, 500), 9_800)
                    responses.append(TopScoreResponse(
                        run=run,
                        question=question,
                        selected_choice=selected_choice,
                        sequence=sequence,
                        response_time_ms=response_time,
                        is_correct=correct,
                    ))
                    if not correct:
                        end_reason = TopScoreRun.EndReason.WRONG_ANSWER
                        break
                    score += 1

                TopScoreResponse.objects.bulk_create(responses)
                run.score = score
                run.status = TopScoreRun.Status.FINISHED
                run.end_reason = end_reason
                run.ended_at = timezone.now()
                run.save()
                created_runs += 1
                created_responses += len(responses)

        self.stdout.write(self.style.SUCCESS(
            f'Replaced synthetic cohort: {player_count} disabled demo accounts, '
            f'{created_runs} runs, {created_responses} responses.'
        ))
        self.stdout.write(self.style.WARNING(
            'These generated outcomes are experimental only and must not be presented '
            'as real player data or evidence of improved learning.'
        ))
