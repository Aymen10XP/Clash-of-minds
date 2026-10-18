import json
import base64
import binascii
import re
from json import JSONDecodeError

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import ProfileUpdateForm, RegistrationForm
from quiz.models import Topic


PROFILE_PHOTO_MAX_BYTES = 5 * 1024 * 1024
PROFILE_PHOTO_DATA_URL = re.compile(r'^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/]+={0,2})$')


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
        'profilePhoto': user.profile_photo.url if user.profile_photo else None,
        'favoriteTopic': user.favorite_topic.slug if user.favorite_topic_id else None,
    }


def _profile_photo_file(photo_data):
    if not photo_data:
        return None, None
    match = PROFILE_PHOTO_DATA_URL.fullmatch(str(photo_data))
    if not match:
        return None, 'Choose a JPEG, PNG, or WebP image.'
    try:
        photo_bytes = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        return None, 'The selected image could not be read.'
    if not photo_bytes or len(photo_bytes) > PROFILE_PHOTO_MAX_BYTES:
        return None, 'Profile photos may be up to 5 MB.'
    image_type = match.group(1)
    valid_signature = (
        (image_type == 'image/jpeg' and photo_bytes.startswith(b'\xff\xd8\xff'))
        or (image_type == 'image/png' and photo_bytes.startswith(b'\x89PNG\r\n\x1a\n'))
        or (image_type == 'image/webp' and photo_bytes.startswith(b'RIFF') and photo_bytes[8:12] == b'WEBP')
    )
    if not valid_signature:
        return None, 'The selected file is not a valid supported image.'
    extension = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}[image_type]
    return ContentFile(photo_bytes, name=f'profile-photo.{extension}'), None


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

    photo_file, photo_error = _profile_photo_file(data.get('profilePhoto'))
    if photo_error:
        return JsonResponse({'errors': {'profilePhoto': [photo_error]}}, status=400)

    try:
        user = form.save()
        if photo_file:
            user.profile_photo.save(photo_file.name, photo_file, save=True)
    except IntegrityError:
        return JsonResponse(
            {'errors': {'email': ['An account with this email already exists.']}},
            status=400,
        )
    return JsonResponse({'user': _user_payload(user)}, status=201)


@require_POST
def update_profile_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sign in to edit your profile.'}, status=401)
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    form = ProfileUpdateForm({'username': data.get('username', '')}, instance=request.user)
    if not form.is_valid():
        return JsonResponse({'errors': _form_errors(form)}, status=400)

    photo_file, photo_error = _profile_photo_file(data.get('profilePhoto'))
    if photo_error:
        return JsonResponse({'errors': {'profilePhoto': [photo_error]}}, status=400)

    favorite_topic = request.user.favorite_topic
    if 'favoriteTopic' in data:
        favorite_topic_slug = data.get('favoriteTopic')
        favorite_topic = None
        if favorite_topic_slug:
            if not isinstance(favorite_topic_slug, str):
                return JsonResponse({'errors': {'favoriteTopic': ['Choose a valid topic.']}}, status=400)
            try:
                favorite_topic = Topic.objects.get(slug=favorite_topic_slug, is_active=True)
            except Topic.DoesNotExist:
                return JsonResponse({'errors': {'favoriteTopic': ['Choose a valid topic.']}}, status=400)
    user = form.save()
    user.favorite_topic = favorite_topic
    user.save(update_fields=('favorite_topic',))
    previous_photo = user.profile_photo.name if user.profile_photo else ''
    if photo_file:
        user.profile_photo.save(photo_file.name, photo_file, save=True)
        if previous_photo:
            user.profile_photo.storage.delete(previous_photo)
    elif data.get('removeProfilePhoto') and previous_photo:
        user.profile_photo.delete(save=True)

    return JsonResponse({'user': _user_payload(user)})


@require_GET
def favorite_topic_players_view(request, topic_slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sign in to view players.'}, status=401)
    try:
        topic = Topic.objects.get(slug=topic_slug, is_active=True)
    except Topic.DoesNotExist:
        return JsonResponse({'error': 'The selected topic is not available.'}, status=404)

    players = get_user_model().objects.filter(
        favorite_topic=topic,
        is_active=True,
    ).exclude(pk=request.user.pk).order_by('username')
    return JsonResponse({
        'topic': {'slug': topic.slug, 'title': topic.title},
        'players': [
            {
                'id': player.pk,
                'username': player.username,
                'country': player.country,
                'profilePhoto': player.profile_photo.url if player.profile_photo else None,
            }
            for player in players[:50]
        ],
    })


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
