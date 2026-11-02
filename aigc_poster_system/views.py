"""
项目级视图
"""
from django.shortcuts import render

from feedback.models import SystemNotice


def home_view(request):
    """首页：展示系统最新公告（需求 5.5 用户登录后可在首页查看公告）"""
    notices = SystemNotice.objects.filter(is_active=True).order_by('-priority', '-created_at')[:5]
    return render(request, 'home.html', {'notices': notices})
