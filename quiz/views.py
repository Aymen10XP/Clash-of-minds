import json
import random
from datetime import timedelta
from json import JSONDecodeError

from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import AnswerChoice, Question, TopScoreResponse, TopScoreRun


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


def _best_score(user):
    return TopScoreRun.objects.filter(user=user).aggregate(best=Max('score'))['best'] or 0


def _next_question(run):
    active = Question.objects.filter(is_active=True).select_related('topic').prefetch_related('choices')
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

    now = timezone.now()
    TopScoreRun.objects.filter(user=request.user, status=TopScoreRun.Status.ACTIVE).update(
        status=TopScoreRun.Status.ABANDONED,
        end_reason=TopScoreRun.EndReason.QUIT,
        ended_at=now,
        current_question=None,
        question_started_at=None,
    )

    run = TopScoreRun.objects.create(user=request.user)
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
