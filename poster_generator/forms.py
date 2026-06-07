"""
海报生成表单
"""
from django import forms
from .models import PosterProject, PosterTemplate


class PosterGenerateForm(forms.Form):
    """海报生成表单"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入海报标题'
        }),
        label='海报标题'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '描述您想要的海报内容、主题或用途'
        }),
        label='海报描述'
    )
    
    custom_prompt = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '（可选）输入自定义提示词，如不输入将自动根据您的画像生成'
        }),
        label='自定义提示词（可选）'
    )
    
    # 内容类型
    content_type = forms.ChoiceField(
        choices=[
            ('', '自动选择（根据用户画像）'),
            ('promotion', '促销广告'),
            ('event', '活动宣传'),
            ('brand', '品牌展示'),
            ('social', '社交媒体'),
            ('poster', '艺术海报'),
            ('business', '商务宣传'),
            ('personal', '个人分享'),
            ('holiday', '节日祝福'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='内容类型'
    )
    
    # 风格覆盖
    style_override = forms.ChoiceField(
        choices=[
            ('', '使用用户画像偏好'),
            ('minimalist', '极简主义'),
            ('vintage', '复古风格'),
            ('modern', '现代简约'),
            ('colorful', '色彩丰富'),
            ('dark', '暗黑风格'),
            ('fresh', '清新自然'),
            ('tech', '科技未来'),
            ('hand_drawn', '手绘插画'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='风格选择（覆盖画像偏好）'
    )
    
    # 高级选项
    use_custom_copy = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='使用自定义文案'
    )
    
    custom_copy = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '输入您想要显示在海报上的文案'
        }),
        label='自定义文案'
    )


class PosterEditForm(forms.ModelForm):
    """海报编辑表单"""

    LAYOUT_CHOICES = [
        ('center', '居中'),
        ('bottom', '底部'),
        ('top', '顶部'),
        ('overlay', '叠加层'),
    ]

    TEXT_COLOR_CHOICES = [
        ('#FFFFFF', '白色'),
        ('#000000', '黑色'),
        ('#FFD700', '金色'),
        ('#FF6B6B', '红色'),
        ('#4FC3F7', '蓝色'),
        ('#A5D6A7', '绿色'),
    ]

    layout = forms.ChoiceField(
        choices=LAYOUT_CHOICES,
        initial='center',
        required=False,
        label='文案位置',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    text_color = forms.ChoiceField(
        choices=TEXT_COLOR_CHOICES,
        initial='#FFFFFF',
        required=False,
        label='文字颜色',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = PosterProject
        fields = ['title', 'description', 'generated_copy']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'generated_copy': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': '海报标题',
            'description': '海报描述',
            'generated_copy': '海报文案 (JSON格式)',
        }


class PosterFeedbackForm(forms.Form):
    """海报反馈表单"""
    satisfaction = forms.ChoiceField(
        choices=[
            (5, '⭐⭐⭐⭐⭐ 非常满意'),
            (4, '⭐⭐⭐⭐ 满意'),
            (3, '⭐⭐⭐ 一般'),
            (2, '⭐⭐ 不满意'),
            (1, '⭐ 非常不满意'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='满意度评分'
    )
    
    feedback_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '请告诉我们您对这张海报的看法，或希望如何改进...'
        }),
        label='详细反馈（可选）'
    )
    
    # 调整参数
    adjust_style = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='调整风格'
    )
    
    adjust_color = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='调整色彩'
    )
    
    adjust_layout = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='调整布局'
    )
    
    adjust_copy = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='调整文案'
    )


class PosterFilterForm(forms.Form):
    """海报筛选表单"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜索海报标题'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', '全部状态'),
            ('completed', '已完成'),
            ('editing', '编辑中'),
            ('failed', '生成失败'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    favorites_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
