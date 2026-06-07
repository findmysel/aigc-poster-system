"""
海报生成Admin配置
"""
from django.contrib import admin
from .models import PosterTemplate, PosterProject, PosterDraft, GenerationTask


@admin.register(PosterTemplate)
class PosterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'style', 'is_active', 'created_at']
    list_filter = ['style', 'is_active']
    search_fields = ['name', 'description']


@admin.register(PosterProject)
class PosterProjectAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'status', 'is_favorite',
        'user_satisfaction', 'created_at'
    ]
    list_filter = ['status', 'is_favorite', 'created_at']
    search_fields = ['title', 'user__username', 'user_prompt']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PosterDraft)
class PosterDraftAdmin(admin.ModelAdmin):
    list_display = ['project', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(GenerationTask)
class GenerationTaskAdmin(admin.ModelAdmin):
    list_display = ['project', 'task_type', 'status', 'created_at', 'completed_at']
    list_filter = ['task_type', 'status', 'created_at']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
