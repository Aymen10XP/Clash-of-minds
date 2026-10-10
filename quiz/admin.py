from django.contrib import admin

from .models import AnswerChoice, Question, Topic, TopScoreResponse, TopScoreRun


class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    extra = 4
    max_num = 4


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('short_prompt', 'topic', 'difficulty', 'is_active', 'updated_at')
    list_filter = ('is_active', 'difficulty', 'topic')
    search_fields = ('prompt', 'explanation')
    inlines = (AnswerChoiceInline,)

    @admin.display(description='Question')
    def short_prompt(self, question):
        return str(question)


@admin.register(TopScoreRun)
class TopScoreRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'status', 'end_reason', 'started_at', 'ended_at')
    list_filter = ('status', 'end_reason')
    search_fields = ('user__username', 'user__email', 'client_run_id')
    readonly_fields = ('client_run_id', 'started_at')


@admin.register(TopScoreResponse)
class TopScoreResponseAdmin(admin.ModelAdmin):
    list_display = ('run', 'sequence', 'question', 'is_correct', 'response_time_ms')
    list_filter = ('is_correct',)
    search_fields = ('run__user__username', 'question__prompt')
    readonly_fields = ('is_correct', 'answered_at')
