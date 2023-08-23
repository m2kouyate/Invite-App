from django.contrib import admin
from .models import CustomUser, InviteCode, AuthCode

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'phone_number', 'invite_code', 'used_invite_code')
    search_fields = ('username', 'phone_number')
    list_filter = ('is_staff', 'is_active')
    ordering = ('-date_joined',)

class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'creator')
    search_fields = ('code', 'creator__username')
    raw_id_fields = ('creator',)

class AuthCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'created_at')
    search_fields = ('phone_number', 'code')
    ordering = ('-created_at',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(InviteCode, InviteCodeAdmin)
admin.site.register(AuthCode, AuthCodeAdmin)
