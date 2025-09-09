# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import (
    CustomUser, UserActivity, EmailVerificationToken, 
    PasswordResetToken, SiteSettings
)

User = get_user_model()

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'email_verified', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'bio', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Account Status', {'fields': ('is_premium', 'email_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'user__username', 'action']
    readonly_fields = ['timestamp', 'user_agent']

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'expires_at', 'used']
    list_filter = ['created_at', 'expires_at', 'used']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'phone_number']
    fieldsets = (
        ('General Settings', {
            'fields': ('site_name', 'site_description')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'phone_number', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'whatsapp_url', 'twitter_url', 'instagram_url', 'linkedin_url')
        }),
        ('Analytics & Maintenance', {
            'fields': ('google_analytics_id', 'maintenance_mode', 'maintenance_message')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance of SiteSettings
        return SiteSettings.objects.count() == 0
    
    def has_delete_permission(self, request, obj=None):
        return False