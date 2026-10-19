from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


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
