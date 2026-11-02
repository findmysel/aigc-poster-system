"""演示数据种子：创建演示账号、公告，并用系统自身的生成流程产出两张不同画像的示例海报。

在 Codespaces 或本地演示环境中由 scripts/run_codespace.sh 自动调用（幂等，可重复运行）。
无智谱 Key 时走系统降级链路（模板文案 + 占位图），链路与真实生成完全一致。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aigc_poster_system.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from feedback.models import SystemNotice
from poster_generator.models import PosterProject
from user_profile.models import UserProfile


def main():
    user, created = User.objects.get_or_create(
        username='demo', defaults={'email': 'demo@example.com'})
    if created:
        user.set_password('Demo@12345')
        user.save()
    SystemNotice.objects.get_or_create(
        title='欢迎使用海报工坊',
        defaults={'content': '欢迎使用海报工坊！在这里你可以结合自己的偏好画像，让 AI 为你生成个性化海报。',
                  'is_active': True})

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.preferred_style:
        profile.preferred_style = 'minimalist'
        profile.preferred_color = 'cool'
        profile.preferred_content = 'event'
        profile.save()

    if PosterProject.objects.filter(user=user).exists():
        print('seed: demo data already exists, skip generation')
        return

    client = Client()
    assert client.login(username='demo', password='Demo@12345'), 'demo login failed'
    # 同一主题、两种画像覆盖参数：提示词与成品风格应明显不同（导师验收示例）
    variants = [
        {'style_override': 'minimalist', 'color_override': 'cool'},
        {'style_override': 'hand_drawn', 'color_override': 'warm'},
    ]
    for v in variants:
        resp = client.post('/poster/generate/', data={
            'title': '校园音乐节',
            'description': '校园音乐节海报',
            'custom_prompt': '',
            'content_type': 'event',
            'style_override': v['style_override'],
            'color_override': v['color_override'],
            'tone': 'casual',
            'size': 'portrait',
            'custom_copy': '',
        })
        print('seed: generate', v, '->', resp.status_code)
    print('seed: posters =', PosterProject.objects.filter(user=user).count())


if __name__ == '__main__':
    main()
