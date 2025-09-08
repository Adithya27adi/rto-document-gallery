from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter = ['role', 'is_verified', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'is_verified', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('email', 'role', 'phone_number')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization_name', 'state', 'created_at']
    search_fields = ['user__email', 'user__username', 'organization_name']
