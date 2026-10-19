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
    favorite_topic = models.ForeignKey(
        'quiz.Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='favorite_players',
    )

    REQUIRED_FIELDS = ['email', 'country']

    def __str__(self):
        return self.username
