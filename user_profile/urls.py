"""
用户画像模块URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_detail, name='profile_detail'),
    path('quick-setup/', views.quick_setup, name='quick_setup'),
    path('prompt-preview/', views.generate_prompt_preview, name='prompt_preview'),
    path('log-behavior/', views.log_behavior, name='log_behavior'),
    path('analysis/', views.profile_analysis, name='profile_analysis'),
]
