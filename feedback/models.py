"""
反馈模型
"""
from django.db import models
from django.contrib.auth.models import User
import json


class Feedback(models.Model):
    """用户反馈"""
    FEEDBACK_TYPES = [
        ('bug', 'Bug报告'),
        ('feature', '功能建议'),
        ('improvement', '改进意见'),
        ('complaint', '投诉'),
        ('other', '其他'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='用户')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, verbose_name='反馈类型')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    
    # 联系方式（可选）
    contact_email = models.EmailField(blank=True, verbose_name='联系邮箱')
    
    # 处理状态
    is_resolved = models.BooleanField(default=False, verbose_name='是否已解决')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')
    resolution = models.TextField(blank=True, verbose_name='处理结果')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = '用户反馈'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SystemNotice(models.Model):
    """系统公告"""
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='是否显示')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '系统公告'
        verbose_name_plural = '系统公告'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
