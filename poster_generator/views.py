"""
海报生成视图
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
import json

from .models import PosterProject, PosterTemplate, PosterDraft, PosterFeedback
from .forms import PosterGenerateForm, PosterEditForm, PosterFeedbackForm, PosterFilterForm
from user_profile.models import UserProfile
from user_profile.behavior import record_behavior, refresh_profile_from_behavior
from .utils.prompt_generator import PromptGenerator
from .utils.image_generator import get_image_generator, SDImageGenerator
from .utils.copy_generator import CopyGenerator, TemplateCopyProvider
from .utils.poster_composer import compose_poster
from .utils.quality_evaluator import evaluate_poster
import io
import logging

logger = logging.getLogger('poster_generator')

POSTER_SIZES = {
    'portrait': (512, 768),
    'landscape': (768, 512),
    'square': (768, 768),
}


@login_required
def poster_list(request):
    """海报列表页"""
    form = PosterFilterForm(request.GET)
    projects = PosterProject.objects.filter(user=request.user)
    
    if form.is_valid():
        data = form.cleaned_data
        
        if data.get('search'):
            projects = projects.filter(title__icontains=data['search'])
        
        if data.get('status'):
            projects = projects.filter(status=data['status'])
        
        if data.get('date_from'):
            projects = projects.filter(created_at__date__gte=data['date_from'])
        
        if data.get('date_to'):
            projects = projects.filter(created_at__date__lte=data['date_to'])
        
        if data.get('favorites_only'):
            projects = projects.filter(is_favorite=True)
    
    # 分页
    paginator = Paginator(projects.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': form,
        'total_count': projects.count(),
    }
    return render(request, 'poster_generator/poster_list.html', context)


@login_required
def generate_poster(request):
    """生成海报页面"""
    # 检查用户画像
    try:
        profile = request.user.profile
        if not profile.preferred_style:
            messages.warning(request, '请先设置您的用户画像，以获得更好的生成效果！')
            return redirect('quick_setup')
    except UserProfile.DoesNotExist:
        messages.warning(request, '请先设置您的用户画像！')
        return redirect('quick_setup')
    
    if request.method == 'POST':
        form = PosterGenerateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # 创建项目
            project = PosterProject.objects.create(
                user=request.user,
                title=data['title'],
                description=data['description'],
                user_prompt=data['custom_prompt'] or data['description'],
                status='generating'
            )
            
            # 保存生成参数
            project.set_generation_params({
                'content_type': data['content_type'] or profile.preferred_content,
                'style_override': data['style_override'],
                'color_override': data.get('color_override', ''),
                'tone': data.get('tone', ''),
                'size': data.get('size') or 'portrait',
                'use_custom_copy': data['use_custom_copy'],
                'custom_copy': data['custom_copy'],
            })
            project.save()
            
            # 执行生成
            success, result = perform_generation(project, profile)
            
            if success:
                messages.success(request, '海报生成成功！')
                if project.get_generation_params().get('used_fallback'):
                    messages.warning(request, '外部模型暂时不可用，已使用备用结果（模板文案/占位图）完成生成。')
                return redirect('poster_detail', project_id=project.id)
            else:
                project.status = 'failed'
                project.save()
                messages.error(request, f'生成失败：{result}')
                return redirect('generate_poster')
    else:
        # 检查是否有复用参数
        reuse_params = request.session.pop('reuse_params', None)
        initial = {}
        if reuse_params:
            initial['content_type'] = reuse_params.get('content_type', '')
            initial['style_override'] = reuse_params.get('style_override', '')
        form = PosterGenerateForm(initial=initial)

    # 获取推荐的模板
    templates = PosterTemplate.objects.filter(is_active=True)[:6]
    
    # 显示画像预览
    generator = PromptGenerator(profile)
    sample_prompts = generator.generate_sample_prompts(count=2)
    
    context = {
        'form': form,
        'templates': templates,
        'profile': profile,
        'sample_prompts': sample_prompts,
    }
    return render(request, 'poster_generator/generate.html', context)


def perform_generation(project, profile):
    """
    执行海报生成（完整链路）：
    用户画像 + 本次参数 -> 个性化提示词 -> 文案生成（GLM-4-Flash，免费）
    -> 图像生成（双后端：智谱 CogView-3-Flash 免费API / 本地 Stable Diffusion）
    -> 海报合成（Pillow，含 description）-> 质量评估 -> 行为落库与画像更新
    模型不可用时降级为模板文案/占位图，不让整单失败（used_fallback 标记）。
    """
    try:
        gen_params = project.get_generation_params()
        content_type = gen_params.get('content_type', '')
        style_override = gen_params.get('style_override', '')
        color_override = gen_params.get('color_override', '')
        tone = gen_params.get('tone', '') or 'professional'
        width, height = POSTER_SIZES.get(gen_params.get('size') or 'portrait', (512, 768))

        # 1. 个性化提示词（基于用户画像 + 本次覆盖参数）
        prompt_gen = PromptGenerator(profile)
        optimized_prompt = prompt_gen.generate_image_prompt(
            project.user_prompt or '',
            content_type=content_type,
            style_override=style_override,
            color_override=color_override,
        )
        # 反馈重新生成时，按反馈调整提示词
        feedback_adjustments = gen_params.get('feedback_adjustments')
        if feedback_adjustments:
            optimized_prompt = prompt_gen.adjust_prompt_by_feedback(optimized_prompt, feedback_adjustments)
        project.optimized_prompt = optimized_prompt
        project.save()

        # 2. 生成图像（双后端可切换，失败自动降级占位图）
        image_gen = get_image_generator()
        project.image_backend = 'sd' if isinstance(image_gen, SDImageGenerator) else 'zhipu'
        success, image_result = image_gen.generate_image(
            optimized_prompt,
            negative_prompt=prompt_gen.generate_negative_prompt(),
            width=width,
            height=height,
        )
        if not success:
            # 生成器内部已降级，这里是极端兜底
            logger.warning('图像生成器返回失败：%s', image_result)
            return False, image_result
        used_fallback = bool(getattr(image_gen, 'used_fallback', False))

        project.generated_image.save(
            f'generated_{project.id}.png',
            image_result,
            save=True
        )

        # 3. 生成文案（反馈重生成优先使用按反馈改过的文案）
        if gen_params.get('regenerated_copy'):
            copy_data = CopyGenerator._fill_defaults(dict(gen_params['regenerated_copy']))
        elif gen_params.get('use_custom_copy'):
            copy_data = CopyGenerator._fill_defaults({
                'headline': gen_params.get('custom_copy', '')[:20] or project.title[:20],
                'subheadline': '',
                'cta': '了解更多',
                'description': '',
            })
        else:
            copy_gen = CopyGenerator()
            copy_result = copy_gen.generate_copy(
                topic=project.title,
                content_type=content_type or 'promotion',
                tone=tone,
                user_profile=profile
            )
            if copy_result['success']:
                copy_data = copy_result['data']
            else:
                copy_data = TemplateCopyProvider.get_random_copy(content_type or 'promotion')
            if not getattr(copy_gen, 'api_key', ''):
                pass  # 无 Key 时 generate_copy 内部已降级为模板文案

        project.generated_copy = json.dumps(copy_data, ensure_ascii=False)
        project.save()

        # 4. 合成海报（图片 + 主标题/副标题/CTA/描述）
        copy_dict = json.loads(project.generated_copy) if isinstance(project.generated_copy, str) else copy_data
        final_poster = compose_poster(
            project.generated_image,
            copy_dict,
            layout='center'
        )

        # 5. 海报质量评估（本地指标：清晰度/对比度/色彩/饱和度/亮度）
        poster_bytes = final_poster.read()
        final_poster.seek(0)
        quality = evaluate_poster(io.BytesIO(poster_bytes))
        project.quality_score = quality.get('score')
        project.set_quality_detail(quality)

        project.final_poster.save(
            f'poster_{project.id}.jpg',
            final_poster,
            save=True
        )

        # 6. 更新状态并记录降级标记
        gen_params = project.get_generation_params()
        gen_params['used_fallback'] = used_fallback
        project.set_generation_params(gen_params)
        project.status = 'completed'
        project.save()

        # 7. 行为数据落库 + 画像动态构建（生成次数/常用标签）
        record_behavior(project.user, 'generate', {
            'project_id': project.id,
            'content_type': content_type,
            'image_backend': project.image_backend,
            'quality_score': project.quality_score,
            'used_fallback': used_fallback,
        })
        refresh_profile_from_behavior(project.user)

        return True, project

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.warning('海报生成异常 project=%s：%s', getattr(project, 'id', '?'), e)
        return False, str(e)


@login_required
def poster_detail(request, project_id):
    """海报详情页"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    
    # 解析文案
    try:
        copy_data = json.loads(project.generated_copy) if project.generated_copy else {}
    except:
        copy_data = {'headline': project.generated_copy, 'subheadline': '', 'cta': ''}
    
    record_behavior(request.user, 'view', {'project_id': project.id})

    context = {
        'project': project,
        'copy_data': copy_data,
        'quality_detail': project.get_quality_detail(),
        'gen_params': project.get_generation_params(),
    }
    return render(request, 'poster_generator/poster_detail.html', context)


@login_required
def edit_poster(request, project_id):
    """编辑海报"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    
    try:
        copy_data = json.loads(project.generated_copy) if project.generated_copy else {}
    except:
        copy_data = {}
    
    if request.method == 'POST':
        form = PosterEditForm(request.POST, instance=project)
        if form.is_valid():
            form.save()

            layout = form.cleaned_data.get('layout') or 'center'
            text_color = form.cleaned_data.get('text_color') or '#FFFFFF'

            # 将布局和颜色写入 generation_params 以便下次回显
            gen_params = project.get_generation_params()
            gen_params['layout'] = layout
            gen_params['text_color'] = text_color
            project.set_generation_params(gen_params)
            project.save()

            try:
                new_copy_data = json.loads(project.generated_copy)
            except Exception:
                new_copy_data = copy_data

            final_poster = compose_poster(
                project.generated_image,
                new_copy_data,
                layout=layout,
                text_color=text_color,
            )

            project.final_poster.save(
                f'poster_{project.id}_edited.jpg',
                final_poster,
                save=True
            )

            record_behavior(request.user, 'edit', {'project_id': project.id})
            messages.success(request, '海报已更新！')
            return redirect('poster_detail', project_id=project.id)
    else:
        # 回填上次保存的布局和颜色
        gen_params = project.get_generation_params()
        initial = {
            'layout': gen_params.get('layout', 'center'),
            'text_color': gen_params.get('text_color', '#FFFFFF'),
        }
        form = PosterEditForm(instance=project, initial=initial)

    context = {
        'project': project,
        'form': form,
        'copy_data': copy_data,
    }
    return render(request, 'poster_generator/edit_poster.html', context)


@login_required
def poster_feedback(request, project_id):
    """海报反馈：评分 + 问题类型 + 文字反馈落独立记录；
    需要调整时新建一条生成记录重新生成，不覆盖原海报（需求 5.4）。"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)

    if request.method == 'POST':
        form = PosterFeedbackForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # 问题类型 -> 调整项映射（选了问题类型但没勾调整项时也能触发重生成）
            type_to_adjust = {
                'copy': 'adjust_copy',
                'style': 'adjust_style',
                'color': 'adjust_color',
                'layout': 'adjust_layout',
                'quality': 'adjust_quality',
            }
            adjustments = {
                'adjust_style': bool(data.get('adjust_style')),
                'adjust_color': bool(data.get('adjust_color')),
                'adjust_layout': bool(data.get('adjust_layout')),
                'adjust_copy': bool(data.get('adjust_copy')),
                'adjust_quality': False,
            }
            fb_type = data.get('feedback_type') or ''
            if fb_type in type_to_adjust:
                adjustments[type_to_adjust[fb_type]] = True

            # 反馈落独立记录（PosterFeedback），同时兼容旧字段
            PosterFeedback.objects.create(
                poster=project,
                user=request.user,
                rating=data['satisfaction'],
                feedback_type=fb_type,
                content=data.get('feedback_text', ''),
            )
            project.user_satisfaction = data['satisfaction']
            project.user_feedback = data['feedback_text']
            project.save()

            try:
                profile = request.user.profile
                profile.update_satisfaction(data['satisfaction'] / 5.0)
            except Exception:
                profile = None

            record_behavior(request.user, 'feedback', {
                'project_id': project.id,
                'rating': data['satisfaction'],
                'feedback_type': fb_type,
            })

            if any(adjustments.values()):
                if profile is None:
                    profile, _ = UserProfile.objects.get_or_create(user=request.user)

                # 新建记录重新生成，原海报保留不覆盖
                new_project = PosterProject.objects.create(
                    user=request.user,
                    title=project.title,
                    description=project.description,
                    user_prompt=project.user_prompt,
                    status='generating',
                    parent_project=project,
                )
                new_params = project.get_generation_params()
                new_params['feedback_adjustments'] = adjustments
                new_params['feedback_text'] = data.get('feedback_text', '')
                new_params['feedback_type'] = fb_type

                # 调整文案时，调用 GLM 按原文案+反馈重新生成文案（无 Key 走模板降级）
                if adjustments.get('adjust_copy'):
                    try:
                        original_copy = json.loads(project.generated_copy) if project.generated_copy else {}
                    except Exception:
                        original_copy = {}
                    regen = CopyGenerator().regenerate_copy(
                        original_copy,
                        data.get('feedback_text') or fb_type or '请优化文案',
                        content_type=new_params.get('content_type') or 'promotion',
                    )
                    if regen.get('success'):
                        new_params['regenerated_copy'] = regen['data']

                new_project.set_generation_params(new_params)
                new_project.save()

                success, result = perform_generation(new_project, profile)
                if success:
                    messages.success(request, '已根据您的反馈重新生成海报（新记录），原海报保留不变！')
                    return redirect('poster_detail', project_id=new_project.id)
                new_project.status = 'failed'
                new_project.save()
                messages.error(request, '重新生成失败，请重试。')
                return redirect('poster_detail', project_id=project.id)
            else:
                messages.success(request, '感谢您的反馈！')

            return redirect('poster_detail', project_id=project.id)
    else:
        form = PosterFeedbackForm()

    context = {
        'project': project,
        'form': form,
    }
    return render(request, 'poster_generator/feedback.html', context)


@login_required
def download_poster(request, project_id):
    """下载海报"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    
    if project.final_poster:
        record_behavior(request.user, 'download', {'project_id': project.id})
        response = FileResponse(project.final_poster.open(), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{project.title}.jpg"'
        return response
    else:
        messages.error(request, '海报文件不存在')
        return redirect('poster_detail', project_id=project.id)


@login_required
@require_POST
def toggle_favorite(request, project_id):
    """切换收藏状态"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    project.is_favorite = not project.is_favorite
    project.save()
    record_behavior(request.user, 'save', {'project_id': project.id, 'is_favorite': project.is_favorite})
    
    return JsonResponse({
        'status': 'success',
        'is_favorite': project.is_favorite
    })


@login_required
@require_POST
def delete_poster(request, project_id):
    """删除海报"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    project.delete()
    messages.success(request, '海报已删除')
    return redirect('poster_list')


@login_required
def reuse_style(request, project_id):
    """
    将指定海报的风格参数（content_type、style_override）存入 session，
    然后跳转到生成页，生成页读取并预填表单。
    """
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    gen_params = project.get_generation_params()
    request.session['reuse_params'] = {
        'content_type': gen_params.get('content_type', ''),
        'style_override': gen_params.get('style_override', ''),
        'from_project_title': project.title,
    }
    messages.info(request, f'已载入「{project.title}」的风格，请填写新海报信息后生成。')
    return redirect('generate_poster')


@login_required
def template_gallery(request):
    """模板库"""
    templates = PosterTemplate.objects.filter(is_active=True)
    
    # 按风格筛选
    style = request.GET.get('style')
    if style:
        templates = templates.filter(style=style)
    
    context = {
        'templates': templates,
        'style_choices': PosterTemplate.STYLE_CHOICES,
    }
    return render(request, 'poster_generator/templates.html', context)
