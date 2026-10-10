import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Topic(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    title = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=240, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ('sort_order', 'title')

    def __str__(self):
        return self.title


class Question(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Easy'
        MEDIUM = 'medium', 'Medium'
        HARD = 'hard', 'Hard'

    topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='questions')
    prompt = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
    )
    is_active = models.BooleanField(
        default=False,
        help_text='Only active questions can be served to a game.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('topic', 'id')
        indexes = [
            models.Index(fields=('is_active', 'topic', 'difficulty')),
        ]

    def clean(self):
        super().clean()
        if not self.is_active:
            return

        if not self.pk:
            raise ValidationError({
                'is_active': 'Save the draft question and its choices before activating it.',
            })

        choice_count = self.choices.count()
        correct_count = self.choices.filter(is_correct=True).count()
        errors = []

        if choice_count != 4:
            errors.append('An active question must have exactly four choices.')
        if correct_count != 1:
            errors.append('An active question must have exactly one correct choice.')
        if errors:
            raise ValidationError({'is_active': errors})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.prompt[:80]


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=300)
    position = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text='Display position from 1 to 4.',
    )
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ('position',)
        constraints = [
            models.UniqueConstraint(
                fields=('question', 'position'),
                name='unique_choice_position_per_question',
            ),
            models.UniqueConstraint(
                fields=('question',),
                condition=Q(is_correct=True),
                name='at_most_one_correct_choice_per_question',
            ),
            models.CheckConstraint(
                condition=Q(position__gte=1, position__lte=4),
                name='choice_position_between_1_and_4',
            ),
        ]

    def clean(self):
        super().clean()
        if not self.question_id:
            return

        siblings = AnswerChoice.objects.filter(question_id=self.question_id).exclude(pk=self.pk)
        total_count = siblings.count() + 1
        correct_count = siblings.filter(is_correct=True).count() + int(self.is_correct)

        if total_count > 4:
            raise ValidationError({'question': 'A question can have only four choices.'})
        if correct_count > 1:
            raise ValidationError({'is_correct': 'A question can have only one correct choice.'})

        if self.question.is_active:
            errors = []
            if total_count != 4:
                errors.append('Deactivate the question before changing its four-choice structure.')
            if correct_count != 1:
                errors.append('An active question must keep exactly one correct choice.')
            if errors:
                raise ValidationError({'question': errors})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.question.is_active:
            raise ValidationError('Deactivate the question before deleting a choice.')
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.position}. {self.text}'


class TopScoreRun(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        FINISHED = 'finished', 'Finished'
        ABANDONED = 'abandoned', 'Abandoned'

    class EndReason(models.TextChoices):
        WRONG_ANSWER = 'wrong_answer', 'Wrong answer'
        TIMEOUT = 'timeout', 'Time expired'
        QUIT = 'quit', 'Player quit'

    client_run_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='top_score_runs',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    end_reason = models.CharField(max_length=20, choices=EndReason.choices, blank=True)
    score = models.PositiveIntegerField(default=0)
    current_question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        blank=True,
    )
    question_started_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-started_at',)
        indexes = [
            models.Index(fields=('user', '-score')),
            models.Index(fields=('status', 'started_at')),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(score__gte=0), name='top_score_run_score_nonnegative'),
            models.CheckConstraint(
                condition=(
                    Q(status='active', ended_at__isnull=True, end_reason='')
                    | Q(status__in=('finished', 'abandoned'), ended_at__isnull=False)
                ),
                name='top_score_run_end_state_consistent',
            ),
        ]

    def clean(self):
        super().clean()
        if self.status == self.Status.ACTIVE:
            if self.ended_at is not None or self.end_reason:
                raise ValidationError('An active run cannot have an end time or end reason.')
            if bool(self.current_question_id) != bool(self.question_started_at):
                raise ValidationError(
                    'An active run must set the current question and its start time together.'
                )
        elif self.ended_at is None or not self.end_reason:
            raise ValidationError('A completed run requires an end time and end reason.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} - {self.score} points'


class TopScoreResponse(models.Model):
    run = models.ForeignKey(TopScoreRun, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name='top_score_responses',
    )
    selected_choice = models.ForeignKey(
        AnswerChoice,
        on_delete=models.PROTECT,
        related_name='top_score_selections',
        null=True,
        blank=True,
        help_text='Empty when the player ran out of time.',
    )
    sequence = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    response_time_ms = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10_000)],
    )
    is_correct = models.BooleanField(default=False, editable=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('sequence',)
        constraints = [
            models.UniqueConstraint(
                fields=('run', 'sequence'),
                name='unique_response_sequence_per_run',
            ),
            models.CheckConstraint(
                condition=Q(sequence__gte=1),
                name='top_score_response_sequence_positive',
            ),
            models.CheckConstraint(
                condition=Q(response_time_ms__gte=0, response_time_ms__lte=10_000),
                name='top_score_response_within_time_limit',
            ),
        ]

    def clean(self):
        super().clean()
        if self.run_id and self.run.status != TopScoreRun.Status.ACTIVE:
            raise ValidationError({'run': 'Responses can only be added to an active run.'})

        if self.selected_choice_id:
            if self.selected_choice.question_id != self.question_id:
                raise ValidationError({
                    'selected_choice': 'The selected choice does not belong to this question.',
                })
            self.is_correct = self.selected_choice.is_correct
        else:
            self.is_correct = False

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'Run {self.run_id}, question {self.sequence}'
