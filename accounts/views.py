import json
import base64
import binascii
import re
from json import JSONDecodeError

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import JsonResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
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
        'favoriteTopics': list(user.favorite_topics.order_by('sort_order', 'title').values_list('slug', flat=True)),
        'isStaff': user.is_staff,
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

    favorite_topics = None
    if 'favoriteTopics' in data:
        topic_slugs = data.get('favoriteTopics')
        if not isinstance(topic_slugs, list) or not 4 <= len(topic_slugs) <= 5:
            return JsonResponse({'errors': {'favoriteTopics': ['Choose between 4 and 5 favorite topics.']}}, status=400)
        if not all(isinstance(slug, str) for slug in topic_slugs) or len(topic_slugs) != len(set(topic_slugs)):
            return JsonResponse({'errors': {'favoriteTopics': ['Favorite topics must be unique and valid.']}}, status=400)
        favorite_topics = list(Topic.objects.filter(slug__in=topic_slugs, is_active=True))
        if len(favorite_topics) != len(topic_slugs):
            return JsonResponse({'errors': {'favoriteTopics': ['Choose only available topics.']}}, status=400)
    user = form.save()
    if favorite_topics is not None:
        user.favorite_topics.set(favorite_topics)
    previous_photo = user.profile_photo.name if user.profile_photo else ''
    if photo_file:
        user.profile_photo.save(photo_file.name, photo_file, save=True)
        if previous_photo:
            user.profile_photo.storage.delete(previous_photo)
    elif data.get('removeProfilePhoto') and previous_photo:
        user.profile_photo.delete(save=True)

    return JsonResponse({'user': _user_payload(user)})


@require_GET
def preference_matches_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sign in to view players.'}, status=401)
    selected = set(request.user.favorite_topics.filter(is_active=True).values_list('slug', flat=True))
    if len(selected) < 4:
        return JsonResponse({'threshold': 75, 'matches': []})

    players = get_user_model().objects.filter(is_active=True).exclude(
        pk=request.user.pk,
    ).prefetch_related(
        Prefetch('favorite_topics', queryset=Topic.objects.filter(is_active=True).order_by('sort_order', 'title')),
    ).order_by('username')
    matches = []
    for player in players:
        player_topics = {topic.slug for topic in player.favorite_topics.all()}
        if len(player_topics) < 4:
            continue
        raw_score = (2 * len(selected & player_topics) / (len(selected) + len(player_topics))) * 100
        if raw_score > 75:
            matches.append({
                'id': player.pk,
                'username': player.username,
                'country': player.country,
                'profilePhoto': player.profile_photo.url if player.profile_photo else None,
                'favoriteTopics': sorted(player_topics),
                'sharedTopics': sorted(selected & player_topics),
                'matchRate': round(raw_score),
            })
    matches.sort(key=lambda match: (-match['matchRate'], match['username'].lower()))
    return JsonResponse({
        'threshold': 75,
        'matches': matches[:50],
    })


def _staff_required(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication is required.'}, status=401)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Administrator access is required.'}, status=403)
    return None


@require_GET
def admin_users_view(request):
    denied = _staff_required(request)
    if denied:
        return denied
    users = get_user_model().objects.order_by('username')
    return JsonResponse({'users': [{
        'id': user.pk,
        'username': user.username,
        'email': user.email,
        'country': user.country,
        'isActive': user.is_active,
        'isStaff': user.is_staff,
    } for user in users]})


@require_POST
def deactivate_user_view(request, user_id):
    denied = _staff_required(request)
    if denied:
        return denied
    if user_id == request.user.pk:
        return JsonResponse({'error': 'You cannot deactivate your own account.'}, status=400)
    try:
        user = get_user_model().objects.get(pk=user_id)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found.'}, status=404)
    if user.is_superuser:
        return JsonResponse({'error': 'A superuser cannot be deactivated here.'}, status=400)
    user.is_active = False
    user.save(update_fields=('is_active',))
    return JsonResponse({'message': 'User deactivated.', 'userId': user.pk, 'isActive': False})


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
def password_reset_request_view(request):
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    email = str(data.get('email', '')).strip()
    if not email:
        return JsonResponse({'errors': {'email': ['Enter your email address.']}}, status=400)

    user = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
    reset_url = None
    if user is not None:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f'{settings.FRONTEND_URL.rstrip("/")}/reset-password/{uid}/{token}'
        send_mail(
            subject='Reset your Clash of Minds password',
            message=(
                f'Hello {user.username},\n\n'
                'Use the link below to choose a new password:\n'
                f'{reset_url}\n\n'
                'If you did not request this change, you can ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

    payload = {
        'message': 'If an active account uses that email, a password reset link has been sent.',
    }
    if settings.DEBUG and reset_url:
        payload['debugResetUrl'] = reset_url
    return JsonResponse(payload)


@require_POST
def password_reset_confirm_view(request):
    data = _read_json(request)
    if data is None:
        return JsonResponse({'error': 'Request body must contain a JSON object.'}, status=400)

    password = str(data.get('password', ''))
    confirm_password = str(data.get('confirmPassword', ''))
    if password != confirm_password:
        return JsonResponse({'errors': {'confirmPassword': ['Passwords do not match.']}}, status=400)

    try:
        user_id = force_str(urlsafe_base64_decode(str(data.get('uid', ''))))
        user = get_user_model().objects.get(pk=user_id, is_active=True)
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError, get_user_model().DoesNotExist):
        user = None

    token = str(data.get('token', ''))
    if user is None or not default_token_generator.check_token(user, token):
        return JsonResponse({'error': 'This password reset link is invalid or has expired.'}, status=400)

    try:
        validate_password(password, user=user)
    except ValidationError as error:
        return JsonResponse({'errors': {'password': list(error.messages)}}, status=400)

    user.set_password(password)
    user.save(update_fields=('password',))
    return JsonResponse({'message': 'Your password has been reset successfully.'})


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
