from django.urls import path

from .views import (
    current_user_view,
    favorite_topic_players_view,
    login_view,
    logout_view,
    register_view,
    update_profile_view,
)


app_name = 'accounts'

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('me/', current_user_view, name='current-user'),
    path('profile/', update_profile_view, name='update-profile'),
    path('favorite-topic/<slug:topic_slug>/players/', favorite_topic_players_view, name='favorite-topic-players'),
]
