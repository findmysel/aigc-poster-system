"""
反馈模块Admin配置
"""
from django.contrib import admin
from .models import Feedback, SystemNotice


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'feedback_type', 'is_resolved', 'created_at']
    list_filter = ['feedback_type', 'is_resolved', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at']


@admin.register(SystemNotice)
class SystemNoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
