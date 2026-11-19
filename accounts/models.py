from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


country_code_validator = RegexValidator(
    regex=r'^[A-Z]{2}$',
    message='Enter a two-letter uppercase ISO 3166-1 country code.',
)


class User(AbstractUser):
    """The account identity used throughout Clash of Minds."""

    email = models.EmailField(unique=True)
    country = models.CharField(
        max_length=2,
        validators=[country_code_validator],
        help_text='Two-letter ISO 3166-1 country code, for example TN or US.',
    )
    profile_photo = models.FileField(upload_to='profile_photos/', blank=True)
    favorite_topics = models.ManyToManyField(
        'quiz.Topic',
        blank=True,
        related_name='favorite_players',
    )

    REQUIRED_FIELDS = ['email', 'country']

    def __str__(self):
        return self.username


class AuditEvent(models.Model):
    """Append-only record of sensitive actions initiated through the application."""

    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_events',
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-created_at', '-pk')

    def __str__(self):
        return f'{self.action} {self.target_type}:{self.target_id}'
