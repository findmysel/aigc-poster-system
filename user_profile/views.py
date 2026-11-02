"""
用户画像视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UserProfile, UserBehaviorLog
from .forms import UserProfileForm, QuickProfileForm
from poster_generator.utils.prompt_generator import PromptGenerator


@login_required
def profile_detail(request):
    """用户画像详情页"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '用户画像已更新！')
            return redirect('profile_detail')
    else:
        form = UserProfileForm(instance=profile)
    
    # 获取行为统计数据
    behavior_stats = {
        'generation_count': profile.generation_count,
        'satisfaction_score': round(profile.satisfaction_score, 2),
        'recent_logs': UserBehaviorLog.objects.filter(user=request.user)[:10]
    }
    
    context = {
        'form': form,
        'profile': profile,
        'stats': behavior_stats,
        'is_new': created
    }
    return render(request, 'user_profile/profile_detail.html', context)


@login_required
def quick_setup(request):
    """快速设置用户画像"""
    if request.method == 'POST':
        form = QuickProfileForm(request.POST)
        if form.is_valid():
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            
            # 根据快速设置自动填充详细画像
            use_case = form.cleaned_data['use_case']
            style_vibe = form.cleaned_data['style_vibe']
            color_mood = form.cleaned_data['color_mood']
            
            # 映射快速设置到详细画像
            profile_map = {
                'personal': {
                    'occupation': 'freelance',
                    'preferred_content': 'personal',
                },
                'business': {
                    'occupation': 'business',
                    'preferred_content': 'business',
                },
                'social': {
                    'occupation': 'media',
                    'preferred_content': 'social',
                },
                'event': {
                    'occupation': 'freelance',
                    'preferred_content': 'event',
                },
            }
            
            style_map = {
                'professional': 'modern',
                'casual': 'fresh',
                'creative': 'hand_drawn',
                'elegant': 'minimalist',
            }
            
            color_map = {
                'bright': 'vibrant',
                'soft': 'pastel',
                'bold': 'warm',
                'calm': 'cool',
            }
            
            # 应用映射
            for key, value in profile_map.get(use_case, {}).items():
                setattr(profile, key, value)
            
            profile.preferred_style = style_map.get(style_vibe, 'modern')
            profile.preferred_color = color_map.get(color_mood, 'neutral')
            
            profile.save()
            messages.success(request, '用户画像设置成功！')
            return redirect('profile_detail')
    else:
        form = QuickProfileForm()
    
    return render(request, 'user_profile/quick_setup.html', {'form': form})


@login_required
def generate_prompt_preview(request):
    """预览根据用户画像生成的提示词"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    generator = PromptGenerator(profile)
    sample_prompts = generator.generate_sample_prompts(count=3)
    
    context = {
        'profile': profile,
        'sample_prompts': sample_prompts
    }
    return render(request, 'user_profile/prompt_preview.html', context)


@login_required
@require_POST
def log_behavior(request):
    """记录用户行为"""
    action = request.POST.get('action')
    details = request.POST.get('details', '{}')
    
    try:
        import json
        details_dict = json.loads(details)
        
        log = UserBehaviorLog.objects.create(
            user=request.user,
            action=action
        )
        log.set_details(details_dict)
        log.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def profile_analysis(request):
    """用户画像分析报告"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # 获取最近的行为记录
    recent_logs = UserBehaviorLog.objects.filter(user=request.user)[:50]
    
    # 统计行为类型
    action_counts = {}
    for log in recent_logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
    
    # 生成个性化建议
    suggestions = []
    if profile.generation_count < 5:
        suggestions.append('您是新用户，建议多尝试不同风格以优化画像')
    if profile.satisfaction_score < 0.7 and profile.generation_count > 0:
        suggestions.append('满意度评分较低，建议调整偏好设置')
    if not profile.preferred_style:
        suggestions.append('建议设置偏好的设计风格以获得更好的生成效果')
    
    # 可视化数据（行为分布/内容与风格分布/质量评分趋势）
    import json as _json
    from .behavior import behavior_stats
    stats = behavior_stats(request.user)

    context = {
        'profile': profile,
        'action_counts': action_counts,
        'suggestions': suggestions,
        'recent_logs': recent_logs[:10],
        'chart_data': _json.dumps(stats, ensure_ascii=False),
        'favorite_tags': profile.get_favorite_tags(),
    }
    return render(request, 'user_profile/analysis.html', context)
