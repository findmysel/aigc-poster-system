"""
海报生成模块URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.poster_list, name='poster_list'),
    path('generate/', views.generate_poster, name='generate_poster'),
    path('<int:project_id>/', views.poster_detail, name='poster_detail'),
    path('<int:project_id>/edit/', views.edit_poster, name='edit_poster'),
    path('<int:project_id>/feedback/', views.poster_feedback, name='poster_feedback'),
    path('<int:project_id>/download/', views.download_poster, name='download_poster'),
    path('<int:project_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:project_id>/delete/', views.delete_poster, name='delete_poster'),
    path('templates/', views.template_gallery, name='template_gallery'),
    path('<int:project_id>/reuse/', views.reuse_style, name='reuse_style'),
]
