"""
反馈视图
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Feedback, SystemNotice
from .forms import FeedbackForm


@login_required
def submit_feedback(request):
    """提交反馈"""
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, '感谢您的反馈！我们会尽快处理。')
            return redirect('feedback_list')
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback/submit.html', {'form': form})


@login_required
def feedback_list(request):
    """反馈列表"""
    feedbacks = Feedback.objects.filter(user=request.user)
    
    paginator = Paginator(feedbacks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'feedback/list.html', {'page_obj': page_obj})


def notices(request):
    """系统公告"""
    notices = SystemNotice.objects.filter(is_active=True)
    return render(request, 'feedback/notices.html', {'notices': notices})


def notice_detail(request, notice_id):
    """系统公告详情"""
    from django.shortcuts import get_object_or_404
    notice = get_object_or_404(SystemNotice, id=notice_id, is_active=True)
    return render(request, 'feedback/notice_detail.html', {'notice': notice})
