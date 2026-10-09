from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class ClashOfMindsUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Clash of Minds', {'fields': ('country',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Clash of Minds', {'fields': ('email', 'country')}),
    )
    list_display = (*UserAdmin.list_display, 'country')
    search_fields = (*UserAdmin.search_fields, 'email')
