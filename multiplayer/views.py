import json
import random
from datetime import timedelta
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from quiz.models import AnswerChoice, Question

from .models import (
    KnowledgeMatch,
    MatchAnswer,
    MatchInvitation,
    MatchParticipant,
    MatchRound,
)


MATCH_DURATION_MS = 5 * 60 * 1000
QUESTION_DURATION_MS = 15 * 1000


def _read_json(request):
    try:
        data = json.loads(request.body or b'{}')
    except (JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _unauthenticated():
    return JsonResponse({'error': 'Authentication is required.'}, status=401)


def _player_payload(player):
    return {
        'id': player.pk,
        'username': player.username,
        'country': player.country,
    }


def _ordered_choices(round_, participant):
    choices = list(round_.question.choices.values('id', 'text').order_by('id'))
    random.Random(f'{round_.match_id}:{round_.sequence}').shuffle(choices)
    if participant.seat == MatchParticipant.Seat.GUEST:
        choices = choices[1:] + choices[:1]
    return choices


def _round_payload(round_, participant):
    answer = round_.answers.filter(participant=participant).first()
    elapsed_ms = max(0, int((timezone.now() - round_.started_at).total_seconds() * 1000))
    return {
        'sequence': round_.sequence,
        'durationMs': QUESTION_DURATION_MS,
        'remainingMs': max(0, QUESTION_DURATION_MS - elapsed_ms),
        'question': {
            'id': round_.question_id,
            'topic': {
                'slug': round_.question.topic.slug,
                'title': round_.question.topic.title,
            },
            'prompt': round_.question.prompt,
            'difficulty': round_.question.difficulty,
            'choices': _ordered_choices(round_, participant),
        },
        'hasAnswered': answer is not None,
        'selectedChoiceId': answer.selected_choice_id if answer else None,
    }


def _match_payload(match, current_user):
    if 'participants' in getattr(match, '_prefetched_objects_cache', {}):
        participants = list(match.participants.all())
    else:
        participants = list(match.participants.select_related('player').all())
    participant = next(item for item in participants if item.player_id == current_user.pk)
    elapsed_ms = 0
    if match.started_at:
        elapsed_ms = max(0, int((timezone.now() - match.started_at).total_seconds() * 1000))
    active_round = match.rounds.filter(status=MatchRound.Status.ACTIVE).select_related(
        'question__topic',
    ).prefetch_related('question__choices', 'answers').first()
    last_round = match.rounds.filter(status=MatchRound.Status.RESOLVED).select_related(
        'question', 'winner__player',
    ).order_by('-sequence').first()
    return {
        'id': str(match.pk),
        'status': match.status,
        'createdAt': match.created_at.isoformat(),
        'startedAt': match.started_at.isoformat() if match.started_at else None,
        'endedAt': match.ended_at.isoformat() if match.ended_at else None,
        'endReason': match.end_reason or None,
        'winnerId': match.winner_id,
        'durationMs': MATCH_DURATION_MS,
        'remainingMs': max(0, MATCH_DURATION_MS - elapsed_ms),
        'participants': [
            {
                **_player_payload(participant.player),
                'seat': participant.seat,
                'score': participant.score,
                'hearts': participant.hearts,
                'ready': participant.is_ready,
                'closed': participant.closed_at is not None,
                'rematchRequested': participant.rematch_requested,
                'isCurrentUser': participant.player_id == current_user.pk,
            }
            for participant in participants
        ],
        'currentRound': _round_payload(active_round, participant) if active_round else None,
        'lastRound': {
            'sequence': last_round.sequence,
            'winnerId': last_round.winner.player_id if last_round.winner_id else None,
            'correctChoiceId': last_round.question.choices.get(is_correct=True).pk,
        } if last_round else None,
        'rematchMatchId': str(match.rematch_match_id) if match.rematch_match_id else None,
    }


def _next_question(match):
    questions = Question.objects.filter(
        is_active=True,
        topic__is_active=True,
    ).select_related('topic').prefetch_related('choices')
    used_ids = match.rounds.values_list('question_id', flat=True)
    available = list(questions.exclude(pk__in=used_ids))
    if not available:
        last_question_id = match.rounds.order_by('-sequence').values_list('question_id', flat=True).first()
        available = list(questions.exclude(pk=last_question_id)) or list(questions)
    return random.choice(available) if available else None


def _create_round(match, question=None):
    question = question or _next_question(match)
    if question is None:
        return None
    sequence = match.rounds.count() + 1
    return MatchRound.objects.create(match=match, question=question, sequence=sequence)


def _finish_match(match, reason, winner_player=None):
    participants = list(match.participants.select_for_update().all())
    if winner_player is None:
        highest_hearts = max(participant.hearts for participant in participants)
        leaders = [participant for participant in participants if participant.hearts == highest_hearts]
        winner_player = leaders[0].player if len(leaders) == 1 else None
    match.status = KnowledgeMatch.Status.COMPLETED
    match.end_reason = reason
    match.winner = winner_player
    match.ended_at = timezone.now()
    match.save(update_fields=('status', 'end_reason', 'winner', 'ended_at'))
    MatchRound.objects.filter(match=match, status=MatchRound.Status.ACTIVE).update(
        status=MatchRound.Status.RESOLVED,
        resolved_at=timezone.now(),
    )


def _expire_match_if_needed(match):
    if (
        match.status == KnowledgeMatch.Status.ACTIVE
        and match.started_at
        and timezone.now() >= match.started_at + timedelta(milliseconds=MATCH_DURATION_MS)
    ):
        _finish_match(match, KnowledgeMatch.EndReason.TIME)
        match.refresh_from_db()
        return True
    return False


def _expire_round_if_needed(match):
    if match.status != KnowledgeMatch.Status.ACTIVE:
        return False
    round_ = match.rounds.filter(status=MatchRound.Status.ACTIVE).select_for_update().first()
    if (
        round_ is not None
        and timezone.now() >= round_.started_at + timedelta(milliseconds=QUESTION_DURATION_MS)
    ):
        _resolve_round(match, round_, _winner_from_answers(round_))
        return True
    return False


def _winner_from_answers(round_):
    correct_answers = list(
        round_.answers.filter(is_correct=True)
        .select_related('participant')
        .order_by('answered_at')
    )
    return correct_answers[0].participant if correct_answers else None


def _resolve_round(match, round_, winner=None):
    round_.status = MatchRound.Status.RESOLVED
    round_.winner = winner
    round_.resolved_at = timezone.now()
    round_.save(update_fields=('status', 'winner', 'resolved_at'))
    if winner is not None:
        winner.score += 1
        winner.save(update_fields=('score',))
        opponent = match.participants.select_for_update().exclude(pk=winner.pk).get()
        opponent.hearts = max(0, opponent.hearts - 1)
        opponent.save(update_fields=('hearts',))
        if opponent.hearts == 0:
            _finish_match(match, KnowledgeMatch.EndReason.HEARTS)
            match.winner = winner.player
            match.save(update_fields=('winner',))
            return
    _create_round(match)


def _invitation_payload(invitation, current_user):
    match_id = None
    try:
        match_id = str(invitation.match.pk)
    except KnowledgeMatch.DoesNotExist:
        pass
    return {
        'id': str(invitation.pk),
        'status': invitation.status,
        'direction': 'incoming' if invitation.recipient_id == current_user.pk else 'outgoing',
        'sender': _player_payload(invitation.sender),
        'recipient': _player_payload(invitation.recipient),
        'createdAt': invitation.created_at.isoformat(),
        'respondedAt': invitation.responded_at.isoformat() if invitation.responded_at else None,
        'matchId': match_id,
    }


@require_GET
def search_players(request):
    if not request.user.is_authenticated:
        return _unauthenticated()
    query = request.GET.get('q', '').strip()[:60]
    players = get_user_model().objects.filter(is_active=True).exclude(pk=request.user.pk)
    if query:
        players = players.filter(username__icontains=query)
    players = players.order_by('username')[:20]
    return JsonResponse({'players': [_player_payload(player) for player in players]})


@require_GET
def invitation_list(request):
    if not request.user.is_authenticated:
        return _unauthenticated()
    invitations = MatchInvitation.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user),
    ).select_related('sender', 'recipient').order_by('-created_at')[:50]
    return JsonResponse({
        'invitations': [
            _invitation_payload(invitation, request.user)
            for invitation in invitations
        ],
    })


@require_POST
@transaction.atomic
def send_invitation(request):
    if not request.user.is_authenticated:
        return _unauthenticated()
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)
    try:
        recipient_id = int(data.get('recipientId'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'recipientId must be an integer.'}, status=400)
    if recipient_id == request.user.pk:
        return JsonResponse({'error': 'You cannot challenge yourself.'}, status=400)

    user_model = get_user_model()
    locked_players = list(
        user_model.objects.select_for_update().filter(
            pk__in=(request.user.pk, recipient_id),
            is_active=True,
        ).order_by('pk')
    )
    recipient = next((player for player in locked_players if player.pk == recipient_id), None)
    if recipient is None:
        return JsonResponse({'error': 'That player is not available.'}, status=404)
    existing = MatchInvitation.objects.filter(
        status=MatchInvitation.Status.PENDING,
    ).filter(
        Q(sender=request.user, recipient=recipient)
        | Q(sender=recipient, recipient=request.user),
    ).first()
    if existing:
        return JsonResponse(
            {'error': 'A pending invitation already exists between these players.'},
            status=409,
        )
    try:
        invitation = MatchInvitation.objects.create(sender=request.user, recipient=recipient)
    except IntegrityError:
        return JsonResponse({'error': 'A pending invitation already exists.'}, status=409)
    return JsonResponse(
        {'invitation': _invitation_payload(invitation, request.user)},
        status=201,
    )


@require_POST
@transaction.atomic
def respond_to_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    data = _read_json(request)
    action = data.get('action') if data is not None else None
    if action not in {'accept', 'decline'}:
        return JsonResponse({'error': 'action must be accept or decline.'}, status=400)

    invitation = get_object_or_404(
        MatchInvitation.objects.select_for_update().select_related('sender', 'recipient'),
        pk=invitation_id,
        recipient=request.user,
    )
    if invitation.status != MatchInvitation.Status.PENDING:
        return JsonResponse({'error': 'This invitation has already been answered.'}, status=409)

    invitation.status = (
        MatchInvitation.Status.ACCEPTED
        if action == 'accept' else MatchInvitation.Status.DECLINED
    )
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=('status', 'responded_at'))

    match = None
    if action == 'accept':
        match = KnowledgeMatch.objects.create(invitation=invitation)
        MatchParticipant.objects.bulk_create([
            MatchParticipant(
                match=match,
                player=invitation.sender,
                seat=MatchParticipant.Seat.HOST,
            ),
            MatchParticipant(
                match=match,
                player=invitation.recipient,
                seat=MatchParticipant.Seat.GUEST,
            ),
        ])
    return JsonResponse({
        'invitation': _invitation_payload(invitation, request.user),
        'match': _match_payload(match, request.user) if match else None,
    })


@require_POST
@transaction.atomic
def cancel_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    invitation = get_object_or_404(
        MatchInvitation.objects.select_for_update().select_related('sender', 'recipient'),
        pk=invitation_id,
        sender=request.user,
    )
    if invitation.status != MatchInvitation.Status.PENDING:
        return JsonResponse({'error': 'Only pending invitations can be cancelled.'}, status=409)
    invitation.status = MatchInvitation.Status.CANCELLED
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=('status', 'responded_at'))
    return JsonResponse({'invitation': _invitation_payload(invitation, request.user)})


@require_GET
def match_list(request):
    if not request.user.is_authenticated:
        return _unauthenticated()
    matches = KnowledgeMatch.objects.filter(
        participants__player=request.user,
        participants__closed_at__isnull=True,
    ).prefetch_related('participants__player').order_by('-created_at')[:25]
    return JsonResponse({
        'matches': [_match_payload(match, request.user) for match in matches],
    })


def _participant_match_or_404(match_id, user):
    return get_object_or_404(
        KnowledgeMatch.objects.prefetch_related('participants__player'),
        pk=match_id,
        participants__player=user,
    )


@require_GET
@transaction.atomic
def match_detail(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    match = get_object_or_404(
        KnowledgeMatch.objects.select_for_update().prefetch_related('participants__player'),
        pk=match_id,
        participants__player=request.user,
    )
    _expire_match_if_needed(match)
    _expire_round_if_needed(match)
    match.refresh_from_db()
    return JsonResponse({'match': _match_payload(match, request.user)})


@require_POST
@transaction.atomic
def set_match_ready(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    match = get_object_or_404(
        KnowledgeMatch.objects.select_for_update(),
        pk=match_id,
        participants__player=request.user,
    )
    if match.status != KnowledgeMatch.Status.WAITING:
        return JsonResponse({'error': 'Readiness can only change before a match starts.'}, status=409)
    participant = MatchParticipant.objects.select_for_update().get(
        match=match,
        player=request.user,
    )
    participant.is_ready = True
    participant.save(update_fields=('is_ready',))
    if not match.participants.filter(is_ready=False).exists():
        question = _next_question(match)
        if question is None:
            return JsonResponse({'error': 'No active quiz questions are available.'}, status=503)
        match.status = KnowledgeMatch.Status.ACTIVE
        match.started_at = timezone.now()
        match.save(update_fields=('status', 'started_at'))
        _create_round(match, question)
    match.refresh_from_db()
    return JsonResponse({'match': _match_payload(match, request.user)})


@require_POST
@transaction.atomic
def submit_match_answer(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)
    try:
        question_id = int(data.get('questionId'))
        choice_id = int(data.get('choiceId'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'questionId and choiceId must be integers.'}, status=400)

    match = get_object_or_404(
        KnowledgeMatch.objects.select_for_update(),
        pk=match_id,
        participants__player=request.user,
    )
    if _expire_match_if_needed(match):
        return JsonResponse({'match': _match_payload(match, request.user)})
    if _expire_round_if_needed(match):
        match.refresh_from_db()
        return JsonResponse({'match': _match_payload(match, request.user)})
    if match.status != KnowledgeMatch.Status.ACTIVE:
        return JsonResponse({'error': 'This match is not active.'}, status=409)
    participant = MatchParticipant.objects.select_for_update().get(
        match=match,
        player=request.user,
    )
    round_ = get_object_or_404(
        MatchRound.objects.select_for_update().select_related('question__topic'),
        match=match,
        status=MatchRound.Status.ACTIVE,
    )
    if round_.question_id != question_id:
        return JsonResponse({'error': 'This is not the current question.'}, status=409)
    existing_answer = MatchAnswer.objects.filter(round=round_, participant=participant).first()
    if existing_answer:
        return JsonResponse({'match': _match_payload(match, request.user)})
    try:
        choice = AnswerChoice.objects.get(pk=choice_id, question_id=question_id)
    except AnswerChoice.DoesNotExist:
        return JsonResponse({'error': 'That answer is not valid for this question.'}, status=400)

    MatchAnswer.objects.create(
        round=round_,
        participant=participant,
        selected_choice=choice,
    )
    if round_.answers.count() == 2:
        _resolve_round(match, round_, _winner_from_answers(round_))
    match.refresh_from_db()
    return JsonResponse({'match': _match_payload(match, request.user)})


@require_POST
@transaction.atomic
def request_rematch(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    match = get_object_or_404(
        KnowledgeMatch.objects.select_for_update(),
        pk=match_id,
        participants__player=request.user,
    )
    if match.status != KnowledgeMatch.Status.COMPLETED:
        return JsonResponse({'error': 'A rematch can only be requested after the duel.'}, status=409)

    participant = MatchParticipant.objects.select_for_update().get(
        match=match,
        player=request.user,
    )
    if participant.closed_at is not None:
        return JsonResponse({'error': 'You already closed this room.'}, status=409)
    if not participant.rematch_requested:
        participant.rematch_requested = True
        participant.save(update_fields=('rematch_requested',))

    participants = list(match.participants.select_for_update().select_related('player').all())
    if match.rematch_match_id is None and all(item.rematch_requested for item in participants):
        host = next(item for item in participants if item.seat == MatchParticipant.Seat.HOST)
        guest = next(item for item in participants if item.seat == MatchParticipant.Seat.GUEST)
        invitation = MatchInvitation.objects.create(
            sender=host.player,
            recipient=guest.player,
            status=MatchInvitation.Status.ACCEPTED,
            responded_at=timezone.now(),
        )
        rematch = KnowledgeMatch.objects.create(invitation=invitation)
        MatchParticipant.objects.bulk_create([
            MatchParticipant(match=rematch, player=host.player, seat=MatchParticipant.Seat.HOST),
            MatchParticipant(match=rematch, player=guest.player, seat=MatchParticipant.Seat.GUEST),
        ])
        match.rematch_match = rematch
        match.save(update_fields=('rematch_match',))

    match.refresh_from_db()
    return JsonResponse({'match': _match_payload(match, request.user)})


@require_POST
@transaction.atomic
def close_match(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    match = get_object_or_404(
        KnowledgeMatch.objects.select_for_update(),
        pk=match_id,
        participants__player=request.user,
    )
    participant = MatchParticipant.objects.select_for_update().get(
        match=match,
        player=request.user,
    )
    if participant.closed_at is None:
        participant.closed_at = timezone.now()
        participant.save(update_fields=('closed_at',))

    if match.status == KnowledgeMatch.Status.ACTIVE:
        opponent = match.participants.select_for_update().exclude(pk=participant.pk).get()
        _finish_match(match, KnowledgeMatch.EndReason.FORFEIT, opponent.player)

    if not match.participants.filter(closed_at__isnull=True).exists():
        match.delete()
        return JsonResponse({'terminated': True, 'match': None})

    return JsonResponse({
        'terminated': False,
        'match': _match_payload(match, request.user),
    })
