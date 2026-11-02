"""
行为数据采集与画像动态构建（导师链路第 1、2 环）

链路：用户行为数据 -> 用户画像构建 -> 个性化提示词生成
- record_behavior：在生成/查看/下载/收藏/编辑/反馈等关键动作处落库
- refresh_profile_from_behavior：用行为与生成记录聚合更新画像——
  生成次数、常用标签（内容类型/风格/色彩频次），供分析页与提示词生成使用
"""
import json
import logging
from collections import Counter

from .models import UserBehaviorLog

logger = logging.getLogger('user_profile')


def record_behavior(user, action, details=None):
    """记录一条用户行为日志，失败不影响主流程"""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        log = UserBehaviorLog.objects.create(user=user, action=action)
        if details:
            log.set_details(details)
            log.save()
        return log
    except Exception as e:
        logger.warning('记录用户行为失败：%s', e)
        return None


def refresh_profile_from_behavior(user):
    """
    根据用户的生成记录聚合更新画像：
    - generation_count = 已生成海报总数（生成即计数，不再依赖评分才+1）
    - favorite_tags = 出现频次最高的内容类型/风格/色彩标签（Top5）
    返回画像对象，失败返回 None。
    """
    try:
        from .models import UserProfile
        from poster_generator.models import PosterProject

        profile, _ = UserProfile.objects.get_or_create(user=user)
        projects = PosterProject.objects.filter(user=user).exclude(status='failed')

        profile.generation_count = projects.count()

        counter = Counter()
        for proj in projects:
            params = proj.get_generation_params()
            for key in ('content_type', 'style_override', 'color_override'):
                value = params.get(key)
                if value:
                    counter[value] += 1
            # 画像偏好本身也计入（代表用户长期偏好）
        if profile.preferred_content:
            counter[profile.preferred_content] += 1
        if profile.preferred_style:
            counter[profile.preferred_style] += 1
        if profile.preferred_color:
            counter[profile.preferred_color] += 1

        profile.set_favorite_tags([tag for tag, _ in counter.most_common(5)])
        profile.save()
        return profile
    except Exception as e:
        logger.warning('行为聚合更新画像失败：%s', e)
        return None


def behavior_stats(user):
    """供可视化展示使用的行为与生成统计（画像分析页图表数据）"""
    from poster_generator.models import PosterProject

    action_counts = Counter(
        UserBehaviorLog.objects.filter(user=user).values_list('action', flat=True))

    projects = PosterProject.objects.filter(user=user).exclude(status='failed')
    content_counter = Counter()
    style_counter = Counter()
    for proj in projects:
        params = proj.get_generation_params()
        if params.get('content_type'):
            content_counter[params['content_type']] += 1
        style = params.get('style_override')
        if style:
            style_counter[style] += 1

    quality_points = list(
        projects.filter(quality_score__isnull=False)
        .order_by('created_at')
        .values_list('created_at', 'quality_score')[:20])
    quality_trend = {
        'labels': [d.strftime('%m-%d %H:%M') for d, _ in quality_points],
        'scores': [round(s, 1) for _, s in quality_points],
    }

    return {
        'action_counts': dict(action_counts),
        'content_counts': dict(content_counter),
        'style_counts': dict(style_counter),
        'quality_trend': quality_trend,
    }
