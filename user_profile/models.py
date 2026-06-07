"""
用户画像模型
"""
from django.db import models
from django.contrib.auth.models import User
import json


class UserProfile(models.Model):
    """
    用户画像模型
    用于存储用户的个性化偏好特征
    """
    # 关联用户
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='用户')
    
    # 基础偏好
    AGE_GROUPS = [
        ('teen', '青少年(13-19岁)'),
        ('young', '青年(20-29岁)'),
        ('adult', '成年(30-49岁)'),
        ('middle', '中年(50-64岁)'),
        ('senior', '老年(65岁以上)'),
    ]
    age_group = models.CharField(max_length=20, choices=AGE_GROUPS, blank=True, verbose_name='年龄段')
    
    GENDER_CHOICES = [
        ('male', '男性'),
        ('female', '女性'),
        ('other', '其他'),
        ('secret', '保密'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name='性别')
    
    OCCUPATION_CHOICES = [
        ('student', '学生'),
        ('it', 'IT/互联网'),
        ('finance', '金融/经济'),
        ('education', '教育/科研'),
        ('medical', '医疗/健康'),
        ('art', '艺术/设计'),
        ('media', '媒体/广告'),
        ('business', '商务/销售'),
        ('freelance', '自由职业'),
        ('other', '其他'),
    ]
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES, blank=True, verbose_name='职业')
    
    # 设计偏好
    STYLE_PREFERENCES = [
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
    preferred_style = models.CharField(max_length=20, choices=STYLE_PREFERENCES, blank=True, verbose_name='偏好的设计风格')
    
    COLOR_PREFERENCES = [
        ('warm', '暖色调'),
        ('cool', '冷色调'),
        ('neutral', '中性色'),
        ('vibrant', '鲜艳色彩'),
        ('monochrome', '单色调'),
        ('pastel', '柔和色调'),
    ]
    preferred_color = models.CharField(max_length=20, choices=COLOR_PREFERENCES, blank=True, verbose_name='偏好的色彩方案')
    
    # 内容偏好
    CONTENT_TYPES = [
        ('promotion', '促销广告'),
        ('event', '活动宣传'),
        ('brand', '品牌展示'),
        ('social', '社交媒体'),
        ('poster', '艺术海报'),
        ('business', '商务宣传'),
        ('personal', '个人分享'),
        ('holiday', '节日祝福'),
    ]
    preferred_content = models.CharField(max_length=20, choices=CONTENT_TYPES, blank=True, verbose_name='偏好的内容类型')
    
    # 高级特征
    font_preference = models.CharField(max_length=100, blank=True, verbose_name='字体偏好')
    layout_preference = models.CharField(max_length=100, blank=True, verbose_name='布局偏好')
    
    # 行为特征（系统自动记录）
    generation_count = models.PositiveIntegerField(default=0, verbose_name='生成次数')
    favorite_tags = models.TextField(default='[]', blank=True, verbose_name='常用标签')
    
    def get_favorite_tags(self):
        try:
            return json.loads(self.favorite_tags)
        except:
            return []
    
    def set_favorite_tags(self, tags):
        self.favorite_tags = json.dumps(tags, ensure_ascii=False)
    satisfaction_score = models.FloatField(default=0, verbose_name='满意度评分')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户画像'
        verbose_name_plural = '用户画像'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} 的用户画像"
    
    def update_satisfaction(self, new_score):
        """更新满意度评分"""
        if self.generation_count == 0:
            self.satisfaction_score = new_score
        else:
            # 加权平均
            total = self.satisfaction_score * self.generation_count + new_score
            self.satisfaction_score = total / (self.generation_count + 1)
        self.generation_count += 1
        self.save()


class UserBehaviorLog(models.Model):
    """
    用户行为日志
    用于记录用户的行为数据，优化画像
    """
    ACTION_TYPES = [
        ('generate', '生成海报'),
        ('edit', '编辑海报'),
        ('save', '保存海报'),
        ('download', '下载海报'),
        ('feedback', '提交反馈'),
        ('adjust', '调整参数'),
        ('view', '浏览海报'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_logs', verbose_name='用户')
    action = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='行为类型')
    details = models.TextField(default='{}', blank=True, verbose_name='详细信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    def get_details(self):
        try:
            return json.loads(self.details)
        except:
            return {}
    
    def set_details(self, detail_dict):
        self.details = json.dumps(detail_dict, ensure_ascii=False)
    
    class Meta:
        verbose_name = '用户行为日志'
        verbose_name_plural = '用户行为日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()}"
