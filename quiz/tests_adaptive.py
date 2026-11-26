"""Tests for the adaptive selector's cold-start and treatment assignment."""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from quiz.adaptive import choose_selection_mode, select_adaptive_question
from quiz.adaptive_features import feature_vector, history_probability
from quiz.models import TopScoreRun


class AdaptiveFeatureTests(SimpleTestCase):
    """Cover the history-based estimate used before a neural model is available."""

    def test_estimate_uses_player_accuracy_and_response_time(self):
        slow_low_accuracy = feature_vector(
            'medium',
            {'count': 10, 'correct': 2, 'average_time_ms': 8_000},
            {'count': 5, 'correct': 1, 'average_time_ms': 8_000},
            {},
        )
        fast_high_accuracy = feature_vector(
            'medium',
            {'count': 10, 'correct': 9, 'average_time_ms': 2_000},
            {'count': 5, 'correct': 5, 'average_time_ms': 2_000},
            {},
        )

        self.assertGreater(
            history_probability(fast_high_accuracy),
            history_probability(slow_low_accuracy),
        )

    def test_cold_start_selects_a_question_in_the_challenge_band(self):
        topic = SimpleNamespace(slug='science')
        questions = [
            SimpleNamespace(pk=index, topic_id=1, topic=topic, difficulty=difficulty)
            for index, difficulty in enumerate(('easy', 'medium', 'hard') * 3, start=1)
        ]
        features = [feature_vector(question.difficulty, {}, {}, {}) for question in questions]

        with patch('quiz.adaptive._feature_context', return_value=features):
            selected, mode = select_adaptive_question(
                SimpleNamespace(pk=1),
                questions,
                TopScoreRun.SelectionMode.HISTORY,
            )

        self.assertEqual(mode, TopScoreRun.SelectionMode.HISTORY)
        selected_features = feature_vector(selected.difficulty, {}, {}, {})
        self.assertGreaterEqual(history_probability(selected_features), 0.45)
        self.assertLessEqual(history_probability(selected_features), 0.85)


class AdaptiveAssignmentTests(SimpleTestCase):
    """Ensure control, history, and available neural runs are labeled correctly."""

    @patch('quiz.adaptive.random.random', return_value=0.05)
    def test_assigns_randomized_control_within_configured_share(self, _random):
        with patch('quiz.adaptive.neural_model_available', return_value=False):
            self.assertEqual(
                choose_selection_mode(),
                TopScoreRun.SelectionMode.RANDOM_CONTROL,
            )

    @patch('quiz.adaptive.random.random', return_value=0.90)
    def test_uses_history_fallback_when_no_model_is_available(self, _random):
        with patch('quiz.adaptive.neural_model_available', return_value=False):
            self.assertEqual(
                choose_selection_mode(),
                TopScoreRun.SelectionMode.HISTORY,
            )

    @patch('quiz.adaptive.random.random', return_value=0.90)
    def test_activates_neural_mode_only_when_a_model_is_available(self, _random):
        with patch('quiz.adaptive.neural_model_available', return_value=True):
            self.assertEqual(
                choose_selection_mode(),
                TopScoreRun.SelectionMode.NEURAL,
            )
