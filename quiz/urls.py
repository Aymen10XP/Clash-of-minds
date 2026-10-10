from django.urls import path

from .views import answer_top_score, quit_top_score, start_top_score


urlpatterns = [
    path('top-score/start/', start_top_score, name='top-score-start'),
    path('top-score/<uuid:client_run_id>/answer/', answer_top_score, name='top-score-answer'),
    path('top-score/<uuid:client_run_id>/quit/', quit_top_score, name='top-score-quit'),
]
