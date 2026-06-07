"""
用户画像Admin配置
"""
from django.contrib import admin
from .models import UserProfile, UserBehaviorLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'age_group', 'gender', 'occupation', 
        'preferred_style', 'preferred_color', 'generation_count', 
        'satisfaction_score', 'updated_at'
    ]
    list_filter = [
        'age_group', 'gender', 'occupation',
        'preferred_style', 'preferred_color', 'created_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['generation_count', 'satisfaction_score', 'created_at', 'updated_at']


@admin.register(UserBehaviorLog)
class UserBehaviorLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['user', 'action', 'details', 'created_at']
