"""
反馈表单
"""
from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """用户反馈表单"""
    
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'title', 'content', 'contact_email']
        widgets = {
            'feedback_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入反馈标题'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '请详细描述您的问题或建议...'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '（可选）如需回复请留下邮箱'
            }),
        }
        labels = {
            'feedback_type': '反馈类型',
            'title': '标题',
            'content': '详细内容',
            'contact_email': '联系邮箱（可选）',
        }
