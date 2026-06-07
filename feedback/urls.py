"""
反馈模块URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.feedback_list, name='feedback_list'),
    path('submit/', views.submit_feedback, name='submit_feedback'),
    path('notices/', views.notices, name='notices'),
]
