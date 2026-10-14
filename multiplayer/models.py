import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q


class MatchInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_match_invitations',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_match_invitations',
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('recipient', 'status', '-created_at')),
            models.Index(fields=('sender', 'status', '-created_at')),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(sender=F('recipient')),
                name='match_invitation_players_differ',
            ),
            models.UniqueConstraint(
                fields=('sender', 'recipient'),
                condition=Q(status='pending'),
                name='one_pending_invitation_per_direction',
            ),
        ]

    def clean(self):
        super().clean()
        if self.sender_id and self.sender_id == self.recipient_id:
            raise ValidationError('A player cannot invite themselves.')

    def __str__(self):
        return f'{self.sender} to {self.recipient} ({self.status})'


class KnowledgeMatch(models.Model):
    class Status(models.TextChoices):
        WAITING = 'waiting', 'Waiting for players'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.OneToOneField(
        MatchInvitation,
        on_delete=models.PROTECT,
        related_name='match',
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.WAITING)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [models.Index(fields=('status', '-created_at'))]

    def __str__(self):
        return f'Match {self.pk} ({self.status})'


class MatchParticipant(models.Model):
    class Seat(models.TextChoices):
        HOST = 'host', 'Host'
        GUEST = 'guest', 'Guest'

    match = models.ForeignKey(
        KnowledgeMatch,
        on_delete=models.CASCADE,
        related_name='participants',
    )
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='knowledge_matches',
    )
    seat = models.CharField(max_length=8, choices=Seat.choices)
    score = models.PositiveIntegerField(default=0)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('seat',)
        constraints = [
            models.UniqueConstraint(fields=('match', 'player'), name='unique_player_per_match'),
            models.UniqueConstraint(fields=('match', 'seat'), name='unique_seat_per_match'),
            models.CheckConstraint(condition=Q(score__gte=0), name='match_score_nonnegative'),
        ]

    def __str__(self):
        return f'{self.player} in {self.match_id}'
