from django.urls import path

from .views import (
    current_user_view,
    admin_users_view,
    deactivate_user_view,
    login_view,
    logout_view,
    preference_matches_view,
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
    path('matches/', preference_matches_view, name='preference-matches'),
    path('admin/users/', admin_users_view, name='admin-users'),
    path('admin/users/<int:user_id>/deactivate/', deactivate_user_view, name='deactivate-user'),
]
