from django.contrib import admin

from .models import KnowledgeMatch, MatchAnswer, MatchInvitation, MatchParticipant, MatchRound


class MatchParticipantInline(admin.TabularInline):
    model = MatchParticipant
    extra = 0
    readonly_fields = ('joined_at',)


class MatchRoundInline(admin.TabularInline):
    model = MatchRound
    extra = 0
    readonly_fields = ('started_at', 'resolved_at')


@admin.register(MatchInvitation)
class MatchInvitationAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'status', 'created_at', 'responded_at')
    list_filter = ('status',)
    search_fields = ('sender__username', 'recipient__username')
    readonly_fields = ('id', 'created_at', 'responded_at')


@admin.register(KnowledgeMatch)
class KnowledgeMatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'started_at', 'ended_at')
    list_filter = ('status',)
    readonly_fields = ('id', 'created_at')
    inlines = (MatchParticipantInline, MatchRoundInline)


@admin.register(MatchAnswer)
class MatchAnswerAdmin(admin.ModelAdmin):
    list_display = ('round', 'participant', 'selected_choice', 'is_correct', 'answered_at')
    list_filter = ('is_correct',)
    readonly_fields = ('is_correct', 'answered_at')
