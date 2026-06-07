"""
用户模块Admin配置
"""
from django.contrib import admin
from .models import UserExtension


@admin.register(UserExtension)
class UserExtensionAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at', 'updated_at']
    search_fields = ['user__username', 'phone']
    list_filter = ['created_at']
