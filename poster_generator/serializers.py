"""
海报生成模块 REST API 序列化器
"""
from rest_framework import serializers
from .models import PosterProject, PosterTemplate
import json


class PosterTemplateSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    class Meta:
        model = PosterTemplate
        fields = ['id', 'name', 'description', 'style', 'tags', 'is_active', 'created_at']

    def get_tags(self, obj):
        return obj.get_tags()


class PosterProjectListSerializer(serializers.ModelSerializer):
    """海报列表序列化器（轻量版）"""
    generated_image_url = serializers.SerializerMethodField()
    final_poster_url = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PosterProject
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'is_favorite', 'generated_image_url', 'final_poster_url',
            'created_at', 'updated_at',
        ]

    def get_generated_image_url(self, obj):
        if obj.generated_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.generated_image.url) if request else obj.generated_image.url
        return None

    def get_final_poster_url(self, obj):
        if obj.final_poster:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.final_poster.url) if request else obj.final_poster.url
        return None


class PosterProjectDetailSerializer(PosterProjectListSerializer):
    """海报详情序列化器（完整版）"""
    copy_data = serializers.SerializerMethodField()
    generation_params = serializers.SerializerMethodField()

    class Meta(PosterProjectListSerializer.Meta):
        fields = PosterProjectListSerializer.Meta.fields + [
            'user_prompt', 'optimized_prompt', 'generated_copy', 'copy_data',
            'generation_params', 'user_satisfaction', 'user_feedback',
        ]

    def get_copy_data(self, obj):
        if obj.generated_copy:
            try:
                return json.loads(obj.generated_copy)
            except Exception:
                return {'headline': obj.generated_copy}
        return {}

    def get_generation_params(self, obj):
        return obj.get_generation_params()


class PosterCreateSerializer(serializers.Serializer):
    """创建海报序列化器"""
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    content_type = serializers.ChoiceField(
        choices=['', 'promotion', 'event', 'brand', 'social', 'poster', 'business', 'personal', 'holiday'],
        required=False, default=''
    )
    style_override = serializers.ChoiceField(
        choices=['', 'minimalist', 'vintage', 'modern', 'colorful', 'dark', 'fresh', 'tech', 'hand_drawn'],
        required=False, default=''
    )
    use_custom_copy = serializers.BooleanField(required=False, default=False)
    custom_copy = serializers.CharField(required=False, allow_blank=True, default='')


class PosterEditSerializer(serializers.Serializer):
    """编辑海报序列化器"""
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    generated_copy = serializers.CharField(required=False, allow_blank=True)
    layout = serializers.ChoiceField(
        choices=['center', 'bottom', 'top', 'overlay'],
        required=False, default='center'
    )
    text_color = serializers.ChoiceField(
        choices=['#FFFFFF', '#000000', '#FFD700', '#FF6B6B', '#4FC3F7', '#A5D6A7'],
        required=False, default='#FFFFFF'
    )


class FeedbackSerializer(serializers.Serializer):
    """反馈序列化器"""
    satisfaction = serializers.IntegerField(min_value=1, max_value=5)
    feedback_text = serializers.CharField(required=False, allow_blank=True, default='')
    adjust_style = serializers.BooleanField(required=False, default=False)
    adjust_color = serializers.BooleanField(required=False, default=False)
    adjust_layout = serializers.BooleanField(required=False, default=False)
    adjust_copy = serializers.BooleanField(required=False, default=False)
    feedback_type = serializers.CharField(required=False, allow_blank=True, default='')
