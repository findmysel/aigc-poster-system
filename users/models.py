"""
用户模型扩展
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserExtension(models.Model):
    """用户扩展信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extension', verbose_name='用户')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    bio = models.TextField(max_length=500, blank=True, verbose_name='个人简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户扩展信息'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.user.username} 的扩展信息"


@receiver(post_save, sender=User)
def create_user_extension(sender, instance, created, **kwargs):
    """创建用户时自动创建扩展信息"""
    if created:
        UserExtension.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_extension(sender, instance, **kwargs):
    """保存用户时同时保存扩展信息"""
    instance.extension.save()
