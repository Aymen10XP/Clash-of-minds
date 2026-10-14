import json
from json import JSONDecodeError

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import KnowledgeMatch, MatchInvitation, MatchParticipant


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


def _match_payload(match, current_user):
    if 'participants' in getattr(match, '_prefetched_objects_cache', {}):
        participants = list(match.participants.all())
    else:
        participants = list(match.participants.select_related('player').all())
    return {
        'id': str(match.pk),
        'status': match.status,
        'createdAt': match.created_at.isoformat(),
        'startedAt': match.started_at.isoformat() if match.started_at else None,
        'participants': [
            {
                **_player_payload(participant.player),
                'seat': participant.seat,
                'score': participant.score,
                'ready': participant.is_ready,
                'isCurrentUser': participant.player_id == current_user.pk,
            }
            for participant in participants
        ],
    }


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
def match_detail(request, match_id):
    if not request.user.is_authenticated:
        return _unauthenticated()
    match = _participant_match_or_404(match_id, request.user)
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
        match.status = KnowledgeMatch.Status.ACTIVE
        match.started_at = timezone.now()
        match.save(update_fields=('status', 'started_at'))
    match.refresh_from_db()
    return JsonResponse({'match': _match_payload(match, request.user)})
