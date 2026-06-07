"""
用户画像表单
"""
from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """用户画像表单"""
    
    class Meta:
        model = UserProfile
        fields = [
            'age_group', 'gender', 'occupation',
            'preferred_style', 'preferred_color', 'preferred_content',
            'font_preference', 'layout_preference'
        ]
        widgets = {
            'age_group': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'preferred_style': forms.Select(attrs={'class': 'form-select'}),
            'preferred_color': forms.Select(attrs={'class': 'form-select'}),
            'preferred_content': forms.Select(attrs={'class': 'form-select'}),
            'font_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：宋体、黑体、手写体等'
            }),
            'layout_preference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：居中对齐、左对齐、网格布局等'
            }),
        }
        labels = {
            'age_group': '年龄段',
            'gender': '性别',
            'occupation': '职业',
            'preferred_style': '偏好的设计风格',
            'preferred_color': '偏好的色彩方案',
            'preferred_content': '偏好的内容类型',
            'font_preference': '字体偏好（可选）',
            'layout_preference': '布局偏好（可选）',
        }


class QuickProfileForm(forms.Form):
    """快速画像设置表单"""
    use_case = forms.ChoiceField(
        choices=[
            ('personal', '个人使用'),
            ('business', '商业推广'),
            ('social', '社交媒体'),
            ('event', '活动策划'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='使用场景'
    )
    
    style_vibe = forms.ChoiceField(
        choices=[
            ('professional', '专业正式'),
            ('casual', '休闲轻松'),
            ('creative', '创意独特'),
            ('elegant', '优雅精致'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='风格氛围'
    )
    
    color_mood = forms.ChoiceField(
        choices=[
            ('bright', '明亮活力'),
            ('soft', '柔和舒适'),
            ('bold', '大胆醒目'),
            ('calm', '平静沉稳'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='色彩氛围'
    )
