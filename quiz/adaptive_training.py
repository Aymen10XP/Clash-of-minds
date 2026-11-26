"""Build chronological, pre-answer training rows from real quiz history only."""

from collections import defaultdict

from .adaptive_features import feature_vector
from .models import TopScoreResponse, TopScoreRun, Topic


TRAINING_MODES = (
    TopScoreRun.SelectionMode.RANDOM_CONTROL,
    TopScoreRun.SelectionMode.HISTORY,
    TopScoreRun.SelectionMode.NEURAL,
)


def _empty_stats():
    return {'count': 0, 'correct': 0, 'average_time_ms': 5_000.0}


def _record_response(stats, is_correct, response_time_ms):
    previous_count = stats['count']
    stats['count'] += 1
    stats['correct'] += int(is_correct)
    stats['average_time_ms'] = (
        stats['average_time_ms'] * previous_count + response_time_ms
    ) / stats['count']


def build_training_rows():
    """Return chronological features, labels, topic vocabulary, and player IDs.

    Feature values are generated before each response is added to history. Rows
    include only post-launch treatment/control runs, while earlier legacy/offline
    events can still contribute to the player's and question's historical stats.
    """
    topic_slugs = list(Topic.objects.order_by('slug').values_list('slug', flat=True))
    topic_indices = {slug: index + 1 for index, slug in enumerate(topic_slugs)}
    player_stats = defaultdict(_empty_stats)
    player_topic_stats = defaultdict(_empty_stats)
    question_stats = defaultdict(_empty_stats)
    features = []
    topic_ids = []
    labels = []
    player_ids = []

    responses = TopScoreResponse.objects.select_related(
        'run', 'run__user', 'question', 'question__topic',
    ).order_by('answered_at', 'pk')
    for response in responses.iterator(chunk_size=1000):
        player_id = response.run.user_id
        topic_id = response.question.topic_id
        player_key = player_id
        topic_key = (player_id, topic_id)
        player_history = player_stats[player_key]
        topic_history = player_topic_stats[topic_key]
        question_history = question_stats[response.question_id]

        if response.run.selection_mode in TRAINING_MODES:
            features.append(feature_vector(
                response.question.difficulty,
                player_history,
                topic_history,
                question_history,
            ))
            topic_ids.append(topic_indices.get(response.question.topic.slug, 0))
            labels.append(float(response.is_correct))
            player_ids.append(player_id)

        _record_response(player_history, response.is_correct, response.response_time_ms)
        _record_response(topic_history, response.is_correct, response.response_time_ms)
        _record_response(question_history, response.is_correct, response.response_time_ms)

    return topic_slugs, topic_ids, features, labels, player_ids
