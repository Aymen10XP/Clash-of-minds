from django.urls import path

from .views import (
    cancel_invitation,
    invitation_list,
    match_detail,
    match_list,
    respond_to_invitation,
    search_players,
    send_invitation,
    set_match_ready,
)


urlpatterns = [
    path('players/', search_players, name='multiplayer-player-search'),
    path('invitations/', invitation_list, name='multiplayer-invitation-list'),
    path('invitations/send/', send_invitation, name='multiplayer-invitation-send'),
    path('invitations/<uuid:invitation_id>/respond/', respond_to_invitation, name='multiplayer-invitation-respond'),
    path('invitations/<uuid:invitation_id>/cancel/', cancel_invitation, name='multiplayer-invitation-cancel'),
    path('matches/', match_list, name='multiplayer-match-list'),
    path('matches/<uuid:match_id>/', match_detail, name='multiplayer-match-detail'),
    path('matches/<uuid:match_id>/ready/', set_match_ready, name='multiplayer-match-ready'),
]
