"""Tests for opt-in synthetic adaptive training examples."""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from quiz.adaptive import _feature_context
from quiz.adaptive_training import build_training_rows
from quiz.models import AnswerChoice, Question, TopScoreResponse, TopScoreRun, Topic


class AdaptiveSyntheticDataTests(TestCase):
    """Verify synthetic rows are isolated and the demo generator is repeatable."""

    def setUp(self):
        self.topic = Topic.objects.create(slug='demo-history', title='Demo History')

    def test_synthetic_responses_require_explicit_training_opt_in(self):
        question = Question.objects.create(
            topic=self.topic,
            prompt='Synthetic training test question?',
        )
        choices = [
            AnswerChoice.objects.create(
                question=question,
                text=f'Choice {position}',
                position=position,
                is_correct=position == 1,
            )
            for position in range(1, 5)
        ]
        user = get_user_model().objects.create_user(
            username='adaptive_synthetic_test',
            email='adaptive_synthetic_test@example.invalid',
            country='TN',
        )
        run = TopScoreRun.objects.create(
            user=user,
            selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
        )
        TopScoreResponse.objects.create(
            run=run,
            question=question,
            selected_choice=choices[0],
            sequence=1,
            response_time_ms=1_000,
        )

        self.assertEqual(len(build_training_rows()[2]), 0)
        self.assertEqual(len(build_training_rows(include_synthetic=True)[2]), 1)

    def test_synthetic_responses_do_not_change_live_question_history(self):
        question = Question.objects.create(
            topic=self.topic,
            prompt='Question history isolation test?',
        )
        choices = [
            AnswerChoice.objects.create(
                question=question,
                text=f'Choice {position}',
                position=position,
                is_correct=position == 1,
            )
            for position in range(1, 5)
        ]
        real_user = get_user_model().objects.create_user(
            username='adaptive_real_test',
            email='adaptive_real_test@example.invalid',
            country='TN',
        )
        synthetic_user = get_user_model().objects.create_user(
            username='adaptive_synthetic_history_test',
            email='adaptive_synthetic_history_test@example.invalid',
            country='TN',
            is_active=False,
        )
        real_run = TopScoreRun.objects.create(
            user=real_user,
            selection_mode=TopScoreRun.SelectionMode.HISTORY,
        )
        synthetic_run = TopScoreRun.objects.create(
            user=synthetic_user,
            selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
        )
        TopScoreResponse.objects.create(
            run=real_run,
            question=question,
            selected_choice=choices[0],
            sequence=1,
            response_time_ms=2_000,
        )
        TopScoreResponse.objects.create(
            run=synthetic_run,
            question=question,
            selected_choice=choices[1],
            sequence=1,
            response_time_ms=2_000,
        )

        features = _feature_context(real_user, [question])[0]
        self.assertAlmostEqual(features[8], 0.6)

    def test_demo_generator_replaces_only_its_labeled_runs(self):
        for question_index in range(10):
            question = Question.objects.create(
                topic=self.topic,
                prompt=f'Demo generator question {question_index}?',
            )
            for position in range(1, 5):
                AnswerChoice.objects.create(
                    question=question,
                    text=f'Question {question_index}, choice {position}',
                    position=position,
                    is_correct=position == 1,
                )
            question.is_active = True
            question.save()

        output = StringIO()
        call_command(
            'generate_adaptive_demo_data',
            players=8,
            runs_per_player=1,
            questions_per_run=10,
            seed=17,
            stdout=output,
        )
        first_response_count = TopScoreResponse.objects.filter(
            run__selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
        ).count()
        self.assertGreaterEqual(first_response_count, 8)
        self.assertEqual(
            get_user_model().objects.filter(
                username__startswith='adaptive_synthetic_',
                is_active=True,
            ).count(),
            0,
        )

        call_command(
            'generate_adaptive_demo_data',
            players=8,
            runs_per_player=1,
            questions_per_run=10,
            seed=17,
            stdout=StringIO(),
        )
        self.assertEqual(
            TopScoreRun.objects.filter(
                selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
            ).count(),
            8,
        )
        self.assertEqual(
            TopScoreResponse.objects.filter(
                run__selection_mode=TopScoreRun.SelectionMode.SYNTHETIC,
            ).count(),
            first_response_count,
        )

