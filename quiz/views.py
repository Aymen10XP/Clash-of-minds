import json
import random
import uuid
from datetime import timedelta
from json import JSONDecodeError

from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import AnswerChoice, Question, Topic, TopScoreResponse, TopScoreRun


ROUND_TIME_MS = 10_000
NETWORK_GRACE_MS = 750


def _read_json(request):
    try:
        data = json.loads(request.body or b'{}')
    except (JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _unauthenticated():
    return JsonResponse({'error': 'Authentication is required.'}, status=401)


def _staff_required(request):
    if not request.user.is_authenticated:
        return _unauthenticated()
    if not request.user.is_staff:
        return JsonResponse({'error': 'Administrator access is required.'}, status=403)
    return None


def _question_payload(question):
    choices = list(question.choices.values('id', 'text'))
    random.shuffle(choices)
    return {
        'id': question.pk,
        'topic': {
            'slug': question.topic.slug,
            'title': question.topic.title,
        },
        'prompt': question.prompt,
        'difficulty': question.difficulty,
        'choices': choices,
    }


def _offline_question_payload(question):
    payload = _question_payload(question)
    payload['correctChoiceId'] = question.choices.get(is_correct=True).pk
    return payload


def _best_score(user):
    return TopScoreRun.objects.filter(user=user).aggregate(best=Max('score'))['best'] or 0


@require_POST
@transaction.atomic
def create_question_view(request):
    denied = _staff_required(request)
    if denied:
        return denied
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    raw_prompt = data.get('prompt', '')
    raw_explanation = data.get('explanation', '')
    prompt = raw_prompt.strip() if isinstance(raw_prompt, str) else ''
    explanation = raw_explanation.strip() if isinstance(raw_explanation, str) else ''
    choices = data.get('choices')
    difficulty = data.get('difficulty', Question.Difficulty.MEDIUM)
    correct_index = data.get('correctChoiceIndex')
    if not prompt:
        return JsonResponse({'error': 'Question text is required.'}, status=400)
    if difficulty not in Question.Difficulty.values:
        return JsonResponse({'error': 'Choose a valid difficulty.'}, status=400)
    if not isinstance(choices, list) or len(choices) != 4:
        return JsonResponse({'error': 'Exactly four answer choices are required.'}, status=400)
    if not all(isinstance(choice, str) for choice in choices):
        return JsonResponse({'error': 'Answer choices must be text.'}, status=400)
    normalized_choices = [choice.strip() for choice in choices]
    if any(not choice for choice in normalized_choices):
        return JsonResponse({'error': 'Answer choices cannot be empty.'}, status=400)
    if len({choice.casefold() for choice in normalized_choices}) != 4:
        return JsonResponse({'error': 'Answer choices must be unique.'}, status=400)
    if not isinstance(correct_index, int) or isinstance(correct_index, bool) or not 0 <= correct_index < 4:
        return JsonResponse({'error': 'Choose one correct answer.'}, status=400)
    try:
        topic = Topic.objects.get(slug=data.get('topicSlug'), is_active=True)
    except Topic.DoesNotExist:
        return JsonResponse({'error': 'Choose an available topic.'}, status=400)

    question = Question.objects.create(
        topic=topic,
        prompt=prompt,
        explanation=explanation,
        difficulty=difficulty,
        is_active=False,
    )
    for index, choice in enumerate(normalized_choices):
        AnswerChoice.objects.create(
            question=question,
            text=choice,
            position=index + 1,
            is_correct=index == correct_index,
        )
    question.is_active = bool(data.get('isActive', True))
    question.save()
    return JsonResponse({
        'question': {
            'id': question.pk,
            'prompt': question.prompt,
            'topicSlug': topic.slug,
            'difficulty': question.difficulty,
            'isActive': question.is_active,
        },
    }, status=201)


@require_GET
def offline_catalog(request):
    """Return the authenticated player's question pack for local practice."""
    if not request.user.is_authenticated:
        return _unauthenticated()

    questions = Question.objects.filter(
        is_active=True,
        topic__is_active=True,
    ).select_related('topic').prefetch_related('choices')
    return JsonResponse({
        'version': max(
            (question.updated_at.isoformat() for question in questions),
            default='empty',
        ),
        'timeLimitMs': ROUND_TIME_MS,
        'bestScore': _best_score(request.user),
        'questions': [_offline_question_payload(question) for question in questions],
    })


def _parse_offline_answer(raw_answer, sequence):
    if not isinstance(raw_answer, dict):
        raise ValueError('Each answer must be an object.')
    question_id = int(raw_answer.get('questionId'))
    choice_id = raw_answer.get('choiceId')
    choice_id = None if choice_id is None else int(choice_id)
    response_time_ms = int(raw_answer.get('responseTimeMs', 0))
    if not 0 <= response_time_ms <= ROUND_TIME_MS:
        raise ValueError('responseTimeMs is outside the allowed range.')

    question = Question.objects.select_related('topic').get(pk=question_id)
    choice = None
    if choice_id is not None:
        choice = AnswerChoice.objects.get(pk=choice_id, question=question)
    return question, choice, response_time_ms, sequence


@require_POST
@transaction.atomic
def sync_offline_runs(request):
    """Idempotently import locally completed runs and verify their score server-side."""
    if not request.user.is_authenticated:
        return _unauthenticated()

    data = _read_json(request)
    runs = data.get('runs') if data is not None else None
    if not isinstance(runs, list) or len(runs) > 100:
        return JsonResponse({'error': 'runs must be an array containing at most 100 items.'}, status=400)

    synced_ids = []
    for raw_run in runs:
        if not isinstance(raw_run, dict):
            return JsonResponse({'error': 'Each run must be an object.'}, status=400)
        try:
            client_run_id = uuid.UUID(str(raw_run['runId']))
            existing = TopScoreRun.objects.filter(client_run_id=client_run_id).first()
            if existing is not None:
                if existing.user_id != request.user.pk:
                    return JsonResponse({'error': 'A run identifier belongs to another player.'}, status=409)
                synced_ids.append(str(existing.client_run_id))
                continue

            raw_answers = raw_run.get('answers', [])
            if not isinstance(raw_answers, list) or not raw_answers:
                raise ValueError('A completed run must contain at least one answer.')
            parsed_answers = [
                _parse_offline_answer(answer, index)
                for index, answer in enumerate(raw_answers, start=1)
            ]
            topic_slug = raw_run.get('topicSlug')
            topic = Topic.objects.get(slug=topic_slug) if topic_slug else None
            if topic and any(question.topic_id != topic.pk for question, *_ in parsed_answers):
                raise ValueError('An answer does not belong to the selected topic.')

            run = TopScoreRun.objects.create(
                client_run_id=client_run_id,
                user=request.user,
                topic=topic,
            )
            score = 0
            terminal_reason = TopScoreRun.EndReason.QUIT
            for question, choice, response_time_ms, sequence in parsed_answers:
                response = TopScoreResponse.objects.create(
                    run=run,
                    question=question,
                    selected_choice=choice,
                    sequence=sequence,
                    response_time_ms=response_time_ms,
                )
                if not response.is_correct:
                    terminal_reason = (
                        TopScoreRun.EndReason.TIMEOUT
                        if choice is None else TopScoreRun.EndReason.WRONG_ANSWER
                    )
                    break
                score += 1

            run.score = score
            run.status = TopScoreRun.Status.FINISHED
            run.end_reason = terminal_reason
            run.ended_at = timezone.now()
            run.save()
            synced_ids.append(str(run.client_run_id))
        except (KeyError, TypeError, ValueError, Topic.DoesNotExist,
                Question.DoesNotExist, AnswerChoice.DoesNotExist):
            return JsonResponse({'error': 'An offline run contains invalid data.'}, status=400)

    return JsonResponse({
        'syncedRunIds': synced_ids,
        'bestScore': _best_score(request.user),
    })


def _next_question(run):
    active = Question.objects.filter(
        is_active=True,
        topic__is_active=True,
    ).select_related('topic').prefetch_related('choices')
    if run.topic_id:
        active = active.filter(topic_id=run.topic_id)
    answered_ids = run.responses.values_list('question_id', flat=True)
    candidates = list(active.exclude(pk__in=answered_ids))
    if not candidates:
        candidates = list(active.exclude(pk=run.current_question_id))
    if not candidates:
        candidates = list(active)
    return random.choice(candidates) if candidates else None


def _finish_run(run, reason):
    run.status = TopScoreRun.Status.FINISHED
    run.end_reason = reason
    run.ended_at = timezone.now()
    run.current_question = None
    run.question_started_at = None
    run.save()


@require_POST
@transaction.atomic
def start_top_score(request):
    if not request.user.is_authenticated:
        return _unauthenticated()

    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    topic = None
    topic_slug = data.get('topicSlug')
    if topic_slug is not None:
        if not isinstance(topic_slug, str) or not topic_slug.strip():
            return JsonResponse({'error': 'topicSlug must be a non-empty string.'}, status=400)
        try:
            topic = Topic.objects.get(slug=topic_slug.strip(), is_active=True)
        except Topic.DoesNotExist:
            return JsonResponse({'error': 'The selected topic is not available.'}, status=404)

    now = timezone.now()
    TopScoreRun.objects.filter(user=request.user, status=TopScoreRun.Status.ACTIVE).update(
        status=TopScoreRun.Status.ABANDONED,
        end_reason=TopScoreRun.EndReason.QUIT,
        ended_at=now,
        current_question=None,
        question_started_at=None,
    )

    run = TopScoreRun.objects.create(user=request.user, topic=topic)
    question = _next_question(run)
    if question is None:
        _finish_run(run, TopScoreRun.EndReason.QUIT)
        return JsonResponse({'error': 'No active quiz questions are available.'}, status=503)

    run.current_question = question
    run.question_started_at = now
    run.save()

    return JsonResponse({
        'runId': str(run.client_run_id),
        'score': run.score,
        'bestScore': _best_score(request.user),
        'timeLimitMs': ROUND_TIME_MS,
        'question': _question_payload(question),
    }, status=201)


@require_POST
@transaction.atomic
def answer_top_score(request, client_run_id):
    if not request.user.is_authenticated:
        return _unauthenticated()

    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    try:
        run = TopScoreRun.objects.select_for_update().get(
            client_run_id=client_run_id,
            user=request.user,
        )
    except TopScoreRun.DoesNotExist:
        return JsonResponse({'error': 'Top Score run was not found.'}, status=404)

    if run.status != TopScoreRun.Status.ACTIVE or run.current_question_id is None:
        return JsonResponse({'error': 'This Top Score run has already ended.'}, status=409)

    try:
        question_id = int(data.get('questionId'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'questionId must be an integer.'}, status=400)
    if question_id != run.current_question_id:
        return JsonResponse({'error': 'This is not the current question.'}, status=409)

    now = timezone.now()
    elapsed_ms = max(0, int((now - run.question_started_at).total_seconds() * 1000))
    timed_out = elapsed_ms > ROUND_TIME_MS + NETWORK_GRACE_MS or data.get('choiceId') is None
    choice = None

    if not timed_out:
        try:
            choice_id = int(data.get('choiceId'))
            choice = AnswerChoice.objects.get(pk=choice_id, question_id=question_id)
        except (TypeError, ValueError, AnswerChoice.DoesNotExist):
            return JsonResponse({'error': 'choiceId is not valid for this question.'}, status=400)

    correct_choice = AnswerChoice.objects.get(question_id=question_id, is_correct=True)
    response = TopScoreResponse.objects.create(
        run=run,
        question_id=question_id,
        selected_choice=choice,
        sequence=run.responses.count() + 1,
        response_time_ms=min(elapsed_ms, ROUND_TIME_MS),
    )

    if not response.is_correct:
        reason = TopScoreRun.EndReason.TIMEOUT if timed_out else TopScoreRun.EndReason.WRONG_ANSWER
        _finish_run(run, reason)
        return JsonResponse({
            'correct': False,
            'timedOut': timed_out,
            'correctChoiceId': correct_choice.pk,
            'score': run.score,
            'bestScore': _best_score(request.user),
            'gameOver': True,
            'endReason': reason,
        })

    run.score += 1
    next_question = _next_question(run)
    if next_question is None:
        _finish_run(run, TopScoreRun.EndReason.QUIT)
        return JsonResponse({'error': 'No active quiz questions are available.'}, status=503)

    run.current_question = next_question
    run.question_started_at = timezone.now() + timedelta(milliseconds=900)
    run.save()
    return JsonResponse({
        'correct': True,
        'timedOut': False,
        'correctChoiceId': correct_choice.pk,
        'score': run.score,
        'bestScore': max(_best_score(request.user), run.score),
        'gameOver': False,
        'question': _question_payload(next_question),
    })


@require_POST
@transaction.atomic
def quit_top_score(request, client_run_id):
    if not request.user.is_authenticated:
        return _unauthenticated()

    try:
        run = TopScoreRun.objects.select_for_update().get(
            client_run_id=client_run_id,
            user=request.user,
        )
    except TopScoreRun.DoesNotExist:
        return JsonResponse({'error': 'Top Score run was not found.'}, status=404)

    if run.status == TopScoreRun.Status.ACTIVE:
        run.status = TopScoreRun.Status.ABANDONED
        run.end_reason = TopScoreRun.EndReason.QUIT
        run.ended_at = timezone.now()
        run.current_question = None
        run.question_started_at = None
        run.save()
    return JsonResponse({'message': 'Run closed.'})
