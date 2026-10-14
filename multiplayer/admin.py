from django.contrib import admin

from .models import KnowledgeMatch, MatchInvitation, MatchParticipant


class MatchParticipantInline(admin.TabularInline):
    model = MatchParticipant
    extra = 0
    readonly_fields = ('joined_at',)


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
    inlines = (MatchParticipantInline,)
