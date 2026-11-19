from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditEvent, User


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    """Expose audit records for review while preventing edits from the admin UI."""

    list_display = ('created_at', 'actor', 'action', 'target_type', 'target_id')
    list_filter = ('action', 'target_type')
    search_fields = ('actor__username', 'target_id', 'action')
    readonly_fields = ('actor', 'action', 'target_type', 'target_id', 'details', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class ClashOfMindsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Clash of Minds', {'fields': ('country', 'favorite_topics')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Clash of Minds', {'fields': ('email', 'country')}),
    )
    list_display = (*UserAdmin.list_display, 'country', 'is_active')
    list_filter = (*UserAdmin.list_filter, 'country')
    filter_horizontal = ('favorite_topics',)
    search_fields = (*UserAdmin.search_fields, 'email')

    def has_delete_permission(self, request, obj=None):
        return False
