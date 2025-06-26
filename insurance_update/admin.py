from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'client', 'is_active')
    list_filter = ('role', 'client', 'is_active')
    search_fields = ('email', 'name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'role', 'client')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'client', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Client)
admin.site.register(ModelAccessPermission)
admin.site.register(ActivityLog)


@admin.register(InsuranceEdit)
class InsuranceEditAdmin(admin.ModelAdmin):
    list_display = ('payer_name', 'edit_type', 'client', 'version', 'created_at')
    list_filter = ('edit_type', 'client', 'payer_category')
    search_fields = ('payer_name', 'instruction', 'version')


@admin.register(ModifierRule)
class ModifierRuleAdmin(admin.ModelAdmin):
    list_display = ('payer_name', 'code_type', 'client', 'sub_category', 'created_at')
    search_fields = ('payer_name', 'code_list', 'modifier_instruction')
    list_filter = ('code_type', 'client', 'payer_category')
