import json
from json import JSONDecodeError

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import RegistrationForm


def _read_json(request):
    try:
        data = json.loads(request.body or b'{}')
    except (JSONDecodeError, UnicodeDecodeError):
        return None

    return data if isinstance(data, dict) else None


def _form_errors(form):
    return {
        field: [error['message'] for error in field_errors]
        for field, field_errors in form.errors.get_json_data().items()
    }


def _user_payload(user):
    return {
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'country': user.country,
    }


@require_POST
def register_view(request):
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    form = RegistrationForm({
        'username': data.get('username', ''),
        'email': data.get('email', ''),
        'country': data.get('country', ''),
        'password1': data.get('password', ''),
        'password2': data.get('confirmPassword', ''),
    })

    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    try:
        user = form.save()
    except IntegrityError:
        return JsonResponse(
            {'errors': {'email': ['An account with this email already exists.']}},
            status=400,
        )
    return JsonResponse({'user': _user_payload(user)}, status=201)


@require_POST
def login_view(request):
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    identity = str(data.get('identity', '')).strip()
    password = str(data.get('password', ''))
    username = identity

    if '@' in identity:
        user_model = get_user_model()
        matched_user = user_model.objects.filter(email__iexact=identity).first()
        if matched_user is not None:
            username = matched_user.get_username()

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid username, email, or password.'}, status=400)

    login(request, user)
    if not data.get('rememberMe', False):
        request.session.set_expiry(0)

    return JsonResponse({'user': _user_payload(user)})


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out successfully.'})


@ensure_csrf_cookie
@require_GET
def current_user_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False, 'user': None})

    return JsonResponse({
        'authenticated': True,
        'user': _user_payload(request.user),
    })
