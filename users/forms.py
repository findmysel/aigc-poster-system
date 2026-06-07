"""
用户表单
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserExtension


class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'placeholder': '请输入邮箱'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '请输入用户名'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': '请输入密码'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': '请确认密码'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserLoginForm(AuthenticationForm):
    """用户登录表单"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': '请输入用户名'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': '请输入密码'
    }))


class UserUpdateForm(forms.ModelForm):
    """用户信息更新表单"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control'
    }))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class UserExtensionForm(forms.ModelForm):
    """用户扩展信息表单"""
    class Meta:
        model = UserExtension
        fields = ['avatar', 'phone', 'bio']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
