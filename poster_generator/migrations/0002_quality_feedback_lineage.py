from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('poster_generator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='posterproject',
            name='quality_score',
            field=models.FloatField(blank=True, null=True, verbose_name='质量综合评分(0-100)'),
        ),
        migrations.AddField(
            model_name='posterproject',
            name='quality_detail',
            field=models.TextField(blank=True, default='{}', verbose_name='质量评估明细(JSON)'),
        ),
        migrations.AddField(
            model_name='posterproject',
            name='image_backend',
            field=models.CharField(blank=True, max_length=20, verbose_name='图像后端'),
        ),
        migrations.AddField(
            model_name='posterproject',
            name='parent_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='regenerations', to='poster_generator.posterproject', verbose_name='重新生成的来源海报'),
        ),
        migrations.CreateModel(
            name='PosterFeedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(verbose_name='评分(1-5)')),
                ('feedback_type', models.CharField(blank=True, choices=[('copy', '文案不合适'), ('style', '风格不符'), ('color', '颜色不合适'), ('layout', '布局不合理'), ('quality', '图片质量不足'), ('other', '其他')], max_length=20, verbose_name='问题类型')),
                ('content', models.TextField(blank=True, verbose_name='反馈内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('poster', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='poster_generator.posterproject', verbose_name='海报')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poster_feedbacks', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '海报反馈',
                'verbose_name_plural': '海报反馈',
                'ordering': ['-created_at'],
            },
        ),
    ]
