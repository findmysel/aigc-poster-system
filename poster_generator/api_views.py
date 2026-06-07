"""
海报生成模块 REST API 视图
提供 JSON 格式的 RESTful 接口，供前端或第三方调用
"""
import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator

from .models import PosterProject, PosterTemplate
from .serializers import (
    PosterProjectListSerializer,
    PosterProjectDetailSerializer,
    PosterCreateSerializer,
    PosterEditSerializer,
    FeedbackSerializer,
    PosterTemplateSerializer,
)
from user_profile.models import UserProfile
from .views import perform_generation
from .utils.poster_composer import compose_poster


# ── 海报列表 & 创建 ────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_poster_list(request):
    """
    GET  /api/posters/        → 获取当前用户的海报列表（支持分页 & 筛选）
    POST /api/posters/        → 创建并生成新海报
    """
    if request.method == 'GET':
        projects = PosterProject.objects.filter(user=request.user)

        # 筛选
        search = request.query_params.get('search', '')
        if search:
            projects = projects.filter(title__icontains=search)

        status_filter = request.query_params.get('status', '')
        if status_filter:
            projects = projects.filter(status=status_filter)

        favorites_only = request.query_params.get('favorites_only', '')
        if favorites_only in ('1', 'true', 'True'):
            projects = projects.filter(is_favorite=True)

        projects = projects.order_by('-created_at')

        # 分页
        page_size = int(request.query_params.get('page_size', 12))
        page_number = int(request.query_params.get('page', 1))
        paginator = Paginator(projects, page_size)
        page = paginator.get_page(page_number)

        serializer = PosterProjectListSerializer(page.object_list, many=True, context={'request': request})
        return Response({
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_number,
            'results': serializer.data,
        })

    # POST — 创建海报
    serializer = PosterCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # 检查用户画像
    try:
        profile = request.user.profile
        if not profile.preferred_style:
            return Response(
                {'detail': '请先完善用户画像（至少设置偏好风格）'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except UserProfile.DoesNotExist:
        return Response({'detail': '请先创建用户画像'}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    project = PosterProject.objects.create(
        user=request.user,
        title=data['title'],
        description=data.get('description', ''),
        user_prompt=data.get('description', '') or data['title'],
        status='generating',
    )
    project.set_generation_params({
        'content_type': data.get('content_type') or profile.preferred_content,
        'style_override': data.get('style_override', ''),
        'use_custom_copy': data.get('use_custom_copy', False),
        'custom_copy': data.get('custom_copy', ''),
    })
    project.save()

    success, result = perform_generation(project, profile)
    if success:
        out_serializer = PosterProjectDetailSerializer(project, context={'request': request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)
    else:
        project.status = 'failed'
        project.save()
        return Response({'detail': f'生成失败：{result}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── 海报详情 & 编辑 & 删除 ────────────────────────────────────────────────────

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_poster_detail(request, project_id):
    """
    GET    /api/posters/<id>/   → 获取海报详情
    PATCH  /api/posters/<id>/   → 更新海报（标题 / 文案 / 布局 / 颜色）
    DELETE /api/posters/<id>/   → 删除海报
    """
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)

    if request.method == 'GET':
        serializer = PosterProjectDetailSerializer(project, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = PosterEditSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        if 'title' in data:
            project.title = data['title']
        if 'description' in data:
            project.description = data['description']
        if 'generated_copy' in data:
            project.generated_copy = data['generated_copy']

        layout = data.get('layout', 'center')
        text_color = data.get('text_color', '#FFFFFF')

        gen_params = project.get_generation_params()
        gen_params['layout'] = layout
        gen_params['text_color'] = text_color
        project.set_generation_params(gen_params)
        project.save()

        # 重新合成海报
        try:
            copy_dict = json.loads(project.generated_copy) if project.generated_copy else {}
        except Exception:
            copy_dict = {}

        if project.generated_image:
            final_poster = compose_poster(project.generated_image, copy_dict, layout=layout, text_color=text_color)
            project.final_poster.save(f'poster_{project.id}_api.jpg', final_poster, save=True)

        out_serializer = PosterProjectDetailSerializer(project, context={'request': request})
        return Response(out_serializer.data)

    # DELETE
    project.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── 收藏 ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_toggle_favorite(request, project_id):
    """POST /api/posters/<id>/favorite/  → 切换收藏状态"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)
    project.is_favorite = not project.is_favorite
    project.save()
    return Response({'is_favorite': project.is_favorite})


# ── 反馈 ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_poster_feedback(request, project_id):
    """POST /api/posters/<id>/feedback/  → 提交反馈（可触发重新生成）"""
    project = get_object_or_404(PosterProject, id=project_id, user=request.user)

    serializer = FeedbackSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    project.user_satisfaction = data['satisfaction']
    project.user_feedback = data.get('feedback_text', '')
    project.save()

    # 更新画像满意度
    try:
        request.user.profile.update_satisfaction(data['satisfaction'] / 5.0)
    except Exception:
        pass

    needs_regen = any([
        data.get('adjust_style'), data.get('adjust_color'),
        data.get('adjust_layout'), data.get('adjust_copy'),
    ])

    if needs_regen:
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

        success, result = perform_generation(project, request.user.profile)
        if not success:
            return Response({'detail': f'重新生成失败：{result}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    out_serializer = PosterProjectDetailSerializer(project, context={'request': request})
    return Response(out_serializer.data)


# ── 模板库 ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_template_list(request):
    """GET /api/templates/  → 获取海报模板列表"""
    templates = PosterTemplate.objects.filter(is_active=True)
    style = request.query_params.get('style', '')
    if style:
        templates = templates.filter(style=style)

    serializer = PosterTemplateSerializer(templates, many=True, context={'request': request})
    return Response({'results': serializer.data, 'count': templates.count()})


# ── 用户画像摘要（供前端展示画像状态）────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile_summary(request):
    """GET /api/profile/summary/  → 返回当前用户画像的关键字段"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return Response({'detail': '用户画像不存在'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'age_group': profile.age_group,
        'gender': profile.gender,
        'occupation': profile.occupation,
        'preferred_style': profile.preferred_style,
        'preferred_color': profile.preferred_color,
        'preferred_content': profile.preferred_content,
        'generation_count': profile.generation_count,
        'satisfaction_score': round(profile.satisfaction_score, 2),
    })
