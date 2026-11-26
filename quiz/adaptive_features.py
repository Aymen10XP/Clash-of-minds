"""Shared feature encoding for adaptive inference and historical training."""

import math


FEATURE_VERSION = 1
NUMERIC_FEATURE_COUNT = 10
DIFFICULTY_ORDER = ('easy', 'medium', 'hard')
TARGET_ACCURACY = 0.70


def feature_vector(difficulty, player_stats, topic_stats, question_stats):
    """Encode only information available before the current answer is submitted."""
    difficulty_values = [float(difficulty == value) for value in DIFFICULTY_ORDER]
    player_total = int(player_stats.get('count', 0))
    topic_total = int(topic_stats.get('count', 0))
    question_total = int(question_stats.get('count', 0))

    player_accuracy = (int(player_stats.get('correct', 0)) + 2) / (player_total + 4)
    topic_accuracy = (int(topic_stats.get('correct', 0)) + 2) / (topic_total + 4)
    question_accuracy = (int(question_stats.get('correct', 0)) + 2) / (question_total + 4)
    average_time = float(player_stats.get('average_time_ms', 5_000) or 5_000)

    history_values = [
        player_accuracy,
        topic_accuracy,
        min(math.log1p(player_total) / math.log(101), 1.0),
        min(math.log1p(topic_total) / math.log(51), 1.0),
        min(max(average_time / 10_000, 0.0), 1.0),
        question_accuracy,
        min(math.log1p(question_total) / math.log(101), 1.0),
    ]
    return difficulty_values + history_values


def history_probability(features):
    """Return a conservative cold-start estimate when trained weights are absent."""
    difficulty_baselines = {'easy': 0.78, 'medium': 0.58, 'hard': 0.40}
    difficulty_index = max(range(3), key=lambda index: features[index])
    baseline = difficulty_baselines[DIFFICULTY_ORDER[difficulty_index]]
    overall_accuracy, topic_accuracy = features[3], features[4]
    average_time, question_accuracy = features[7], features[8]

    estimate = (
        baseline
        + (overall_accuracy - 0.55) * 0.60
        + (topic_accuracy - 0.55) * 0.75
        + (question_accuracy - baseline) * 0.30
        + (0.50 - average_time) * 0.12
    )
    return min(max(estimate, 0.05), 0.95)
