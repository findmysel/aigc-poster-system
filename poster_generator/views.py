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

from .models import PosterProject, PosterTemplate, PosterDraft
from .forms import PosterGenerateForm, PosterEditForm, PosterFeedbackForm, PosterFilterForm
from user_profile.models import UserProfile
from .utils.prompt_generator import PromptGenerator
from .utils.image_generator import CogViewImageGenerator
from .utils.copy_generator import CopyGenerator, TemplateCopyProvider
from .utils.poster_composer import compose_poster


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
                'use_custom_copy': data['use_custom_copy'],
                'custom_copy': data['custom_copy'],
            })
            project.save()
            
            # 执行生成
            success, result = perform_generation(project, profile)
            
            if success:
                messages.success(request, '海报生成成功！')
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
    执行海报生成
    :param project: PosterProject对象
    :param profile: UserProfile对象
    :return: (success, result)
    """
    try:
        # 1. 生成提示词
        prompt_gen = PromptGenerator(profile)
        
        gen_params = project.get_generation_params()
        content_type = gen_params.get('content_type', '')
        style_override = gen_params.get('style_override', '')
        
        optimized_prompt = prompt_gen.generate_image_prompt(
            project.user_prompt or '',
            content_type=content_type,
            style_override=style_override
        )
        project.optimized_prompt = optimized_prompt
        project.save()
        
        # 2. 生成图像
        image_gen = CogViewImageGenerator()
        success, image_result = image_gen.generate_image(
            optimized_prompt,
            negative_prompt=prompt_gen.generate_negative_prompt()
        )
        
        if not success:
            return False, image_result
        
        # 保存生成的图片
        project.generated_image.save(
            f'generated_{project.id}.png',
            image_result,
            save=True
        )
        
        # 3. 生成文案
        gen_params = project.get_generation_params()
        if gen_params.get('use_custom_copy'):
            copy_data = {
                'headline': gen_params.get('custom_copy', '')[:10],
                'subheadline': '',
                'cta': '了解更多',
            }
        else:
            copy_gen = CopyGenerator()
            copy_result = copy_gen.generate_copy(
                topic=project.title,
                content_type=content_type or 'promotion',
                user_profile=profile
            )
            if copy_result['success']:
                copy_data = copy_result['data']
            else:
                copy_data = TemplateCopyProvider.get_random_copy(content_type or 'promotion')
        
        project.generated_copy = json.dumps(copy_data, ensure_ascii=False)
        project.save()
        
        # 4. 合成海报
        copy_dict = json.loads(project.generated_copy) if isinstance(project.generated_copy, str) else copy_data
        final_poster = compose_poster(
            project.generated_image,
            copy_dict,
            layout='center'
        )
        
        project.final_poster.save(
            f'poster_{project.id}.jpg',
            final_poster,
            save=True
        )
        
        # 5. 更新状态
        project.status = 'completed'
        project.save()
        
        # 6. 更新用户画像统计（generation_count 由 update_satisfaction 维护，此处只保存其他字段）
        profile.save()
        
        return True, project
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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
    
    context = {
        'project': project,
        'copy_data': copy_data,
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
    """海报反馈"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    
    if request.method == 'POST':
        form = PosterFeedbackForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # 保存反馈
            project.user_satisfaction = data['satisfaction']
            project.user_feedback = data['feedback_text']
            project.save()
            
            # 更新用户画像满意度
            try:
                profile = request.user.profile
                profile.update_satisfaction(data['satisfaction'] / 5.0)
            except:
                pass
            
            # 如果需要调整，重新生成
            if data.get('adjust_style') or data.get('adjust_color') or data.get('adjust_layout') or data.get('adjust_copy'):
                # 更新生成参数
                gen_params = project.get_generation_params()
                gen_params['feedback_adjustments'] = {
                    'adjust_style': data.get('adjust_style'),
                    'adjust_color': data.get('adjust_color'),
                    'adjust_layout': data.get('adjust_layout'),
                    'adjust_copy': data.get('adjust_copy'),
                }
                project.set_generation_params(gen_params)
                project.status = 'generating'
                project.save()
                
                # 重新生成
                profile = request.user.profile
                success, result = perform_generation(project, profile)
                
                if success:
                    messages.success(request, '已根据您的反馈重新生成海报！')
                else:
                    messages.error(request, '重新生成失败，请重试。')
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
