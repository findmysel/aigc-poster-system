"""
REST API URL 配置
挂载在 /api/ 前缀下
"""
from django.urls import path
from . import api_views

urlpatterns = [
    # 海报资源
    path('posters/', api_views.api_poster_list, name='api_poster_list'),
    path('posters/<int:project_id>/', api_views.api_poster_detail, name='api_poster_detail'),
    path('posters/<int:project_id>/favorite/', api_views.api_toggle_favorite, name='api_toggle_favorite'),
    path('posters/<int:project_id>/feedback/', api_views.api_poster_feedback, name='api_poster_feedback'),

    # 模板库
    path('templates/', api_views.api_template_list, name='api_template_list'),

    # 用户画像摘要
    path('profile/summary/', api_views.api_user_profile_summary, name='api_profile_summary'),
]
