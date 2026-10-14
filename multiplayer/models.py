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

    class EndReason(models.TextChoices):
        HEARTS = 'hearts', 'A player lost all hearts'
        TIME = 'time', 'Five-minute timer expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.OneToOneField(
        MatchInvitation,
        on_delete=models.PROTECT,
        related_name='match',
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.WAITING)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='won_knowledge_matches',
        null=True,
        blank=True,
    )
    end_reason = models.CharField(max_length=10, choices=EndReason.choices, blank=True)
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
    hearts = models.PositiveSmallIntegerField(default=3)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('seat',)
        constraints = [
            models.UniqueConstraint(fields=('match', 'player'), name='unique_player_per_match'),
            models.UniqueConstraint(fields=('match', 'seat'), name='unique_seat_per_match'),
            models.CheckConstraint(condition=Q(score__gte=0), name='match_score_nonnegative'),
            models.CheckConstraint(
                condition=Q(hearts__gte=0, hearts__lte=3),
                name='match_hearts_between_zero_and_three',
            ),
        ]

    def __str__(self):
        return f'{self.player} in {self.match_id}'


class MatchRound(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        RESOLVED = 'resolved', 'Resolved'

    match = models.ForeignKey(
        KnowledgeMatch,
        on_delete=models.CASCADE,
        related_name='rounds',
    )
    question = models.ForeignKey(
        'quiz.Question',
        on_delete=models.PROTECT,
        related_name='multiplayer_rounds',
    )
    sequence = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    winner = models.ForeignKey(
        MatchParticipant,
        on_delete=models.SET_NULL,
        related_name='won_rounds',
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('sequence',)
        constraints = [
            models.UniqueConstraint(fields=('match', 'sequence'), name='unique_round_sequence'),
            models.UniqueConstraint(
                fields=('match',),
                condition=Q(status='active'),
                name='one_active_round_per_match',
            ),
            models.CheckConstraint(condition=Q(sequence__gte=1), name='match_round_sequence_positive'),
        ]

    def __str__(self):
        return f'Match {self.match_id}, round {self.sequence}'


class MatchAnswer(models.Model):
    round = models.ForeignKey(MatchRound, on_delete=models.CASCADE, related_name='answers')
    participant = models.ForeignKey(
        MatchParticipant,
        on_delete=models.CASCADE,
        related_name='match_answers',
    )
    selected_choice = models.ForeignKey(
        'quiz.AnswerChoice',
        on_delete=models.PROTECT,
        related_name='multiplayer_selections',
    )
    is_correct = models.BooleanField(default=False, editable=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('answered_at',)
        constraints = [
            models.UniqueConstraint(fields=('round', 'participant'), name='one_answer_per_player_round'),
        ]

    def clean(self):
        super().clean()
        if self.participant_id and self.round_id:
            if self.participant.match_id != self.round.match_id:
                raise ValidationError({'participant': 'The player does not belong to this match.'})
        if self.selected_choice_id and self.round_id:
            if self.selected_choice.question_id != self.round.question_id:
                raise ValidationError({'selected_choice': 'The answer does not belong to this question.'})
            self.is_correct = self.selected_choice.is_correct

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.participant} answered round {self.round_id}'
