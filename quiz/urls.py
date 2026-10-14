from django.urls import path

from .views import (
    answer_top_score,
    offline_catalog,
    quit_top_score,
    start_top_score,
    sync_offline_runs,
)


urlpatterns = [
    path('top-score/start/', start_top_score, name='top-score-start'),
    path('offline/catalog/', offline_catalog, name='offline-catalog'),
    path('offline/sync/', sync_offline_runs, name='offline-sync'),
    path('top-score/<uuid:client_run_id>/answer/', answer_top_score, name='top-score-answer'),
    path('top-score/<uuid:client_run_id>/quit/', quit_top_score, name='top-score-quit'),
]
