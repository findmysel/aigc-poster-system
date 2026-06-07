"""
用户视图
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, View
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm, UserExtensionForm
from .models import UserExtension


class RegisterView(CreateView):
    """用户注册视图"""
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '注册成功！请登录。')
        return response


class LoginView(View):
    """用户登录视图"""
    template_name = 'users/login.html'
    
    def get(self, request):
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                return redirect('home')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """用户登出视图"""
    def get(self, request):
        logout(request)
        messages.success(request, '已成功退出登录。')
        return redirect('home')


@login_required
def profile_view(request):
    """用户信息页面"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        extension_form = UserExtensionForm(
            request.POST, 
            request.FILES, 
            instance=request.user.extension
        )
        
        if user_form.is_valid() and extension_form.is_valid():
            user_form.save()
            extension_form.save()
            messages.success(request, '个人信息已更新！')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        extension_form = UserExtensionForm(instance=request.user.extension)
    
    context = {
        'user_form': user_form,
        'extension_form': extension_form
    }
    return render(request, 'users/profile.html', context)
