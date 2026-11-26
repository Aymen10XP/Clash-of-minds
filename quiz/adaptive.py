"""Question scoring, history features, and optional trained-model inference."""

import os
import pickle
import random
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db.models import Avg, Count, Q

from .adaptive_features import (
    FEATURE_VERSION,
    TARGET_ACCURACY,
    feature_vector,
    history_probability,
)
from .models import TopScoreResponse, TopScoreRun


def _model_path():
    configured = getattr(settings, 'ADAPTIVE_MODEL_PATH', None)
    if configured:
        return Path(configured)
    return Path(settings.BASE_DIR) / 'var' / 'adaptive_question_model.pt'


@lru_cache(maxsize=2)
def _load_model(path, modified_ns):
    try:
        import torch

        from .adaptive_network import AdaptiveQuestionNetwork

        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        if checkpoint.get('feature_version') != FEATURE_VERSION:
            return None
        topic_slugs = checkpoint.get('topic_slugs', [])
        model = AdaptiveQuestionNetwork(topic_count=len(topic_slugs) + 1)
        model.load_state_dict(checkpoint['state_dict'])
        model.eval()
        topic_ids = {slug: index + 1 for index, slug in enumerate(topic_slugs)}
        return torch, model, topic_ids
    except (
        ImportError,
        OSError,
        RuntimeError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
        IndexError,
        pickle.UnpicklingError,
    ):
        return None


def _model_bundle():
    path = _model_path()
    try:
        modified_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_model(str(path), modified_ns)


def neural_model_available():
    """Return whether a compatible model artifact can currently be loaded."""
    return _model_bundle() is not None


def choose_selection_mode():
    """Assign a small randomized control group and select the available treatment."""
    try:
        control_rate = float(getattr(settings, 'ADAPTIVE_RANDOM_CONTROL_RATE', 0.10))
    except (TypeError, ValueError):
        control_rate = 0.10
    control_rate = min(max(control_rate, 0.0), 1.0)
    if random.random() < control_rate:
        return TopScoreRun.SelectionMode.RANDOM_CONTROL
    if neural_model_available():
        return TopScoreRun.SelectionMode.NEURAL
    return TopScoreRun.SelectionMode.HISTORY


def _as_stats(aggregate):
    return {
        'count': aggregate.get('count') or 0,
        'correct': aggregate.get('correct') or 0,
        'average_time_ms': aggregate.get('average_time_ms') or 5_000,
    }


def _stats_by(queryset, field):
    rows = queryset.values(field).annotate(
        count=Count('pk'),
        correct=Count('pk', filter=Q(is_correct=True)),
        average_time_ms=Avg('response_time_ms'),
    )
    return {row[field]: _as_stats(row) for row in rows}


def _feature_context(user, questions):
    responses = TopScoreResponse.objects.all()
    player_responses = responses.filter(run__user_id=user.pk)
    player = _as_stats(player_responses.aggregate(
        count=Count('pk'),
        correct=Count('pk', filter=Q(is_correct=True)),
        average_time_ms=Avg('response_time_ms'),
    ))
    by_topic = _stats_by(player_responses, 'question__topic_id')
    by_question = _stats_by(responses, 'question_id')

    features = []
    for question in questions:
        topic_stats = by_topic.get(question.topic_id, _as_stats({}))
        question_stats = by_question.get(question.pk, _as_stats({}))
        features.append(feature_vector(
            question.difficulty,
            player,
            topic_stats,
            question_stats,
        ))
    return features


def _neural_probabilities(questions, features):
    bundle = _model_bundle()
    if bundle is None:
        return None
    torch, model, topic_ids = bundle
    topics = torch.tensor(
        [topic_ids.get(question.topic.slug, 0) for question in questions],
        dtype=torch.long,
    )
    numeric = torch.tensor(features, dtype=torch.float32)
    with torch.inference_mode():
        return torch.sigmoid(model(topics, numeric)).tolist()


def select_adaptive_question(user, questions, preferred_mode):
    """Choose among available questions near the target success probability.

    The neural model is used when the requested treatment has a compatible trained
    artifact. Otherwise it falls back to the explicitly recorded history mode.
    """
    questions = list(questions)
    if not questions:
        return None, preferred_mode

    features = _feature_context(user, questions)
    probabilities = None
    actual_mode = preferred_mode
    if preferred_mode == TopScoreRun.SelectionMode.NEURAL:
        try:
            probabilities = _neural_probabilities(questions, features)
        except (ImportError, OSError, RuntimeError, TypeError, ValueError):
            probabilities = None
        if probabilities is None:
            actual_mode = TopScoreRun.SelectionMode.HISTORY

    if probabilities is None:
        probabilities = [history_probability(row) for row in features]

    ranked = sorted(
        zip(questions, probabilities),
        key=lambda pair: (abs(pair[1] - TARGET_ACCURACY), pair[0].pk),
    )
    # Sample among a few similarly suitable questions to avoid a rigid sequence.
    shortlist = [pair for pair in ranked if pair[1] <= 0.85 and pair[1] >= 0.45][:3]
    if not shortlist:
        shortlist = ranked[:min(3, len(ranked))]
    return random.choice(shortlist)[0], actual_mode


