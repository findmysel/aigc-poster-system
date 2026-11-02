"""
海报生成模型
"""
from django.db import models
from django.contrib.auth.models import User
import os
import uuid
import json


def poster_image_path(instance, filename):
    """生成海报图片存储路径"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('posters', str(instance.user.id), filename)


class PosterTemplate(models.Model):
    """
    海报模板
    系统预设的海报模板
    """
    name = models.CharField(max_length=100, verbose_name='模板名称')
    description = models.TextField(blank=True, verbose_name='模板描述')
    preview_image = models.ImageField(upload_to='templates/', verbose_name='预览图')
    
    # 模板属性
    STYLE_CHOICES = [
        ('minimalist', '极简主义'),
        ('vintage', '复古风格'),
        ('modern', '现代简约'),
        ('colorful', '色彩丰富'),
        ('dark', '暗黑风格'),
        ('fresh', '清新自然'),
        ('tech', '科技未来'),
        ('hand_drawn', '手绘插画'),
        ('3d', '3D立体'),
        ('gradient', '渐变风格'),
    ]
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, verbose_name='风格')
    
    # 模板参数（JSON格式存储布局参数）
    layout_params = models.TextField(default='{}', verbose_name='布局参数')
    
    def get_layout_params(self):
        try:
            return json.loads(self.layout_params)
        except:
            return {}
    
    def set_layout_params(self, params):
        self.layout_params = json.dumps(params, ensure_ascii=False)
    
    # 推荐标签
    tags = models.TextField(default='[]', verbose_name='标签')
    
    def get_tags(self):
        try:
            return json.loads(self.tags)
        except:
            return []
    
    def set_tags(self, tag_list):
        self.tags = json.dumps(tag_list, ensure_ascii=False)
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '海报模板'
        verbose_name_plural = '海报模板'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class PosterProject(models.Model):
    """
    海报生成项目
    记录每次海报生成的完整信息
    """
    STATUS_CHOICES = [
        ('pending', '等待生成'),
        ('generating', '生成中'),
        ('completed', '已完成'),
        ('failed', '生成失败'),
        ('editing', '编辑中'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poster_projects', verbose_name='用户')
    title = models.CharField(max_length=200, verbose_name='海报标题')
    description = models.TextField(blank=True, verbose_name='海报描述')
    
    # 生成状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    
    # 用户输入
    user_prompt = models.TextField(verbose_name='用户输入的提示词')
    
    # AI生成的提示词（经过用户画像优化）
    optimized_prompt = models.TextField(blank=True, verbose_name='优化后的提示词')
    
    # 生成的文案
    generated_copy = models.TextField(blank=True, verbose_name='生成的文案')
    
    # 生成的图片
    generated_image = models.ImageField(upload_to=poster_image_path, blank=True, null=True, verbose_name='生成的图片')
    
    # 最终海报（合成后）
    final_poster = models.ImageField(upload_to=poster_image_path, blank=True, null=True, verbose_name='最终海报')
    
    # 使用的模板
    template = models.ForeignKey(PosterTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='使用模板')
    
    # 生成参数
    generation_params = models.TextField(default='{}', verbose_name='生成参数')
    
    def get_generation_params(self):
        try:
            return json.loads(self.generation_params)
        except:
            return {}
    
    def set_generation_params(self, params):
        self.generation_params = json.dumps(params, ensure_ascii=False)
    
    # 用户反馈
    user_satisfaction = models.IntegerField(null=True, blank=True, verbose_name='用户满意度(1-5)')
    user_feedback = models.TextField(blank=True, verbose_name='用户反馈')
    
    # 是否收藏
    is_favorite = models.BooleanField(default=False, verbose_name='是否收藏')

    # 海报质量评估（导师链路：生成后本地评估，结果存入记录）
    quality_score = models.FloatField(null=True, blank=True, verbose_name='质量综合评分(0-100)')
    quality_detail = models.TextField(default='{}', blank=True, verbose_name='质量评估明细(JSON)')

    def get_quality_detail(self):
        try:
            return json.loads(self.quality_detail)
        except Exception:
            return {}

    def set_quality_detail(self, detail):
        self.quality_detail = json.dumps(detail, ensure_ascii=False)

    # 图像生成后端：zhipu（智谱免费API）/ sd（本地Stable Diffusion）
    image_backend = models.CharField(max_length=20, blank=True, verbose_name='图像后端')

    # 重新生成 lineage：根据反馈重新生成时新建记录并指向原海报，不覆盖原版（需求 5.4）
    parent_project = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='regenerations', verbose_name='重新生成的来源海报')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '海报项目'
        verbose_name_plural = '海报项目'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class PosterDraft(models.Model):
    """
    海报草稿
    用于保存编辑过程中的临时状态
    """
    project = models.OneToOneField(PosterProject, on_delete=models.CASCADE, related_name='draft', verbose_name='关联项目')
    
    # 草稿数据
    draft_data = models.TextField(default='{}', verbose_name='草稿数据')
    
    def get_draft_data(self):
        try:
            return json.loads(self.draft_data)
        except:
            return {}
    
    def set_draft_data(self, data):
        self.draft_data = json.dumps(data, ensure_ascii=False)
    
    # 当前编辑的图片
    current_image = models.ImageField(upload_to='drafts/', blank=True, null=True, verbose_name='当前图片')
    
    # 编辑历史
    edit_history = models.TextField(default='[]', verbose_name='编辑历史')
    
    def get_edit_history(self):
        try:
            return json.loads(self.edit_history)
        except:
            return []
    
    def set_edit_history(self, history):
        self.edit_history = json.dumps(history, ensure_ascii=False)
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '海报草稿'
        verbose_name_plural = '海报草稿'
    
    def __str__(self):
        return f"{self.project.title} 的草稿"


class GenerationTask(models.Model):
    """
    生成任务
    用于异步处理海报生成
    """
    STATUS_CHOICES = [
        ('queued', '队列中'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    project = models.ForeignKey(PosterProject, on_delete=models.CASCADE, related_name='tasks', verbose_name='关联项目')
    task_type = models.CharField(max_length=50, verbose_name='任务类型')  # image, copy, compose
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued', verbose_name='状态')
    
    # 任务参数
    params = models.TextField(default='{}', verbose_name='任务参数')
    
    def get_params(self):
        try:
            return json.loads(self.params)
        except:
            return {}
    
    def set_params(self, param_dict):
        self.params = json.dumps(param_dict, ensure_ascii=False)
    
    # 任务结果
    result = models.TextField(default='{}', blank=True, verbose_name='任务结果')
    
    def get_result(self):
        try:
            return json.loads(self.result)
        except:
            return {}
    
    def set_result(self, result_dict):
        self.result = json.dumps(result_dict, ensure_ascii=False)
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        verbose_name = '生成任务'
        verbose_name_plural = '生成任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project.title} - {self.task_type}"


class PosterFeedback(models.Model):
    """
    海报反馈记录（需求 5.4 / 6.1 PosterFeedback 实体）
    与通用意见反馈（feedback.Feedback）区分：这里是针对单张海报的
    评分 + 问题类型 + 文字反馈，重新生成时保留不覆盖。
    """
    FEEDBACK_TYPE_CHOICES = [
        ('copy', '文案不合适'),
        ('style', '风格不符'),
        ('color', '颜色不合适'),
        ('layout', '布局不合理'),
        ('quality', '图片质量不足'),
        ('other', '其他'),
    ]

    poster = models.ForeignKey(PosterProject, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='海报')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='poster_feedbacks', verbose_name='用户')
    rating = models.IntegerField(verbose_name='评分(1-5)')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, blank=True, verbose_name='问题类型')
    content = models.TextField(blank=True, verbose_name='反馈内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '海报反馈'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 对《{self.poster.title}》的反馈（{self.rating}星）"
