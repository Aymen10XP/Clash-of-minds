from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError


class RegistrationForm(UserCreationForm):
    class Meta: 
        model = get_user_model()
        fields = ('username', 'email', 'country')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        user_model = get_user_model()

        if user_model.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')

        return email

    def clean_country(self):
        return self.cleaned_data['country'].upper()
