"""
图像生成器（双后端可切换，只用免费方案）

后端一：智谱 CogView-3-Flash（免费云端 API，默认）
后端二：本地 Stable Diffusion WebUI API（本地部署，免费无 Key）
通过环境变量 IMAGE_BACKEND 切换：zhipu / sd

降级策略（需求 3.3 / 7.2）：
- 无 Key、接口异常、图片下载失败时，一律降级为渐变占位图继续完成海报，
  不让整单生成失败；同时通过 used_fallback 标记和日志告知调用方。
"""
import base64
import io
import logging
import time

import requests
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger('poster_generator')

# 下载外部图片的大小上限（需求 5.3.4：校验 HTTP 状态、内容类型和文件大小）
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _gradient_fallback(width, height, prefix='placeholder'):
    """生成渐变占位图，返回 (True, ContentFile)"""
    image = Image.new('RGB', (width, height))
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            r = int(100 + 155 * (i / width))
            g = int(100 + 155 * (j / height))
            b = int(150 + 105 * ((i + j) / (width + height)))
            pixels[i, j] = (r, g, b)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return True, ContentFile(buffer.getvalue(), name=f'{prefix}_{int(time.time())}.png')


def _bytes_to_contentfile(content, width, height, prefix):
    """将图片字节统一转 RGB、缩放到目标尺寸、存为 PNG ContentFile。
    校验文件大小（需求 5.3.4），失败抛 ValueError。"""
    if not content:
        raise ValueError('图片内容为空')
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError(f'图片过大：{len(content)} 字节，超过上限 {MAX_IMAGE_BYTES}')
    img = Image.open(io.BytesIO(content)).convert('RGB')
    if img.size != (width, height):
        img = img.resize((width, height), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), name=f'{prefix}_{int(time.time())}.png')


class CogViewImageGenerator:
    """基于智谱 CogView-3-Flash（免费模型）的图像生成器"""

    SIZE_MAP = {
        (512, 768): '768x1344',
        (768, 512): '1344x768',
        (512, 512): '1024x1024',
        (768, 768): '1024x1024',
        (1024, 1024): '1024x1024',
    }
    DEFAULT_SIZE = '768x1344'  # 竖版海报默认尺寸

    def __init__(self):
        self.api_key = getattr(settings, 'ZHIPUAI_API_KEY', '')
        self.model = 'cogview-3-flash'
        self.used_fallback = False
        self.last_error = ''

    def generate_image(self, prompt, negative_prompt='', width=512, height=768, **kwargs):
        """
        生成图像，任何失败都降级为占位图（不再向上返回失败）。
        :return: (True, ContentFile)；是否降级见 self.used_fallback
        """
        self.used_fallback = False
        if not self.api_key:
            self.used_fallback = True
            self.last_error = '未配置 ZHIPUAI_API_KEY'
            logger.info('CogView 未配置 API Key，使用渐变占位图降级')
            return _gradient_fallback(width, height)

        size = self.SIZE_MAP.get((width, height), self.DEFAULT_SIZE)
        cogview_prompt = self._convert_prompt(prompt)

        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key = self.api_key)
            response = client.images.generations(
                model=self.model,
                prompt=cogview_prompt,
                size=size,
            )
            image_url = response.data[0].url
            return self._download_image(image_url, width, height)
        except Exception as e:
            self.used_fallback = True
            self.last_error = str(e)
            logger.warning('CogView 调用失败，降级为占位图：%s', e)
            return _gradient_fallback(width, height)

    def _convert_prompt(self, prompt):
        """将 SD 风格关键词提示词转换为适合 CogView 的中文自然语言描述"""
        content_map = {
            'promotional poster for sales and discounts': '促销打折活动',
            'event announcement poster': '活动宣传',
            'brand identity poster': '品牌宣传',
            'social media post design': '社交媒体',
            'holiday greeting poster': '节日庆典',
            'business professional poster': '商务办公',
            'personal creative poster': '创意个性',
            'artistic poster design': '艺术创作',
            'professional poster design': '专业海报',
        }
        style_map = {
            'minimalist design, clean, simple, elegant, white space, geometric': '极简风格，留白设计，几何图形',
            'vintage style, retro, classic, nostalgic, aged texture, antique': '复古怀旧风格，做旧质感',
            'modern design, contemporary, sleek, professional, trendy': '现代时尚风格，简洁专业',
            'vibrant colors, colorful, energetic, bold, dynamic': '色彩鲜艳，充满活力',
            'dark theme, moody, dramatic, noir, sophisticated, black background': '深色背景，神秘高端',
            'fresh, natural, organic, light, airy, clean, green': '清新自然风格，明亮通透',
            'futuristic, technology, digital, cyber, neon, high-tech': '科技未来感，霓虹光效',
            'hand drawn, illustration, artistic, sketch, watercolor': '手绘插画风格，水彩艺术感',
            '3D render, three-dimensional, depth, realistic, volumetric': '三维立体效果',
            'gradient, smooth transitions, colorful blend, modern gradient': '渐变色彩，色彩过渡自然',
        }
        color_map = {
            'warm colors, red, orange, yellow, cozy, inviting': '暖色调，红橙黄配色',
            'cool colors, blue, green, purple, calm, professional': '冷色调，蓝绿紫配色',
            'neutral colors, beige, gray, brown, balanced, versatile': '中性色调，米灰棕配色',
            'vibrant, saturated colors, bright, eye-catching, bold': '高饱和度，色彩鲜亮夺目',
            'monochrome, black and white, grayscale, elegant, classic': '黑白单色，经典雅致',
            'pastel colors, soft pink, light blue, mint, gentle, soothing': '马卡龙色，柔和粉嫩',
        }
        age_map = {
            'youthful, trendy, energetic, bold, modern': '年轻活力，潮流感十足',
            'fresh, dynamic, contemporary, stylish': '时尚动感，潮流现代',
            'professional, balanced, sophisticated, refined': '专业沉稳，精致优雅',
            'elegant, classic, trustworthy, established': '典雅经典，值得信赖',
            'traditional, clear, simple, readable, warm': '传统温馨，清晰易读',
        }

        desc = prompt
        all_maps = {**content_map, **style_map, **color_map, **age_map}
        for en, zh in all_maps.items():
            desc = desc.replace(en, zh)

        for tag in ['high quality, detailed, 4K, professional design',
                    'high quality', 'detailed', '4K', 'professional design',
                    'price tags, sale badges, discount stickers, shopping elements',
                    'date, time, location icons, decorative elements',
                    'logo placement, brand colors, professional typography',
                    'engaging visuals, share buttons, hashtags, trendy style',
                    'artistic composition, creative layout, visual impact',
                    'corporate style, professional layout, contact info',
                    'personal touch, lifestyle, authentic, relatable',
                    'festive decorations, seasonal elements, celebratory']:
            desc = desc.replace(tag, '')

        import re
        desc = re.sub(r'[a-zA-Z]{3,}', '', desc)
        desc = re.sub(r'[,，\s]+', '，', desc)
        desc = re.sub(r'，+', '，', desc)
        desc = desc.strip('，, ')

        if not desc or len(desc) < 5:
            desc = '现代时尚风格，色彩丰富'

        # 背景图不直接生成大段文字，文字由本地合成器叠加（需求 5.3.4）
        return f"一张精美的海报背景图，{desc}，画面精致，色彩丰富，构图美观，高清质感，不要出现文字"

    def _download_image(self, url, width, height):
        """下载图片：校验 HTTP 状态、内容类型、文件大小；失败降级占位图"""
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            content_type = resp.headers.get('Content-Type', '')
            if content_type and not content_type.startswith('image/'):
                raise ValueError(f'返回内容不是图片：Content-Type={content_type}')
            return True, _bytes_to_contentfile(resp.content, width, height, 'cogview')
        except Exception as e:
            self.used_fallback = True
            self.last_error = str(e)
            logger.warning('CogView 图片下载失败，降级为占位图：%s', e)
            return _gradient_fallback(width, height)

    # 兼容旧调用名
    def _fallback_image(self, width, height):
        self.used_fallback = True
        return _gradient_fallback(width, height)

    def check_api_status(self):
        return bool(self.api_key)


class SDImageGenerator:
    """本地 Stable Diffusion WebUI 图像生成器（导师链路：Stable Diffusion 海报生成）

    依赖本地启动 Stable Diffusion WebUI 并开启 --api，
    接口：POST {SD_API_URL}，即 http://127.0.0.1:7860/sdapi/v1/txt2img
    本地部署、无需 API Key、完全免费。服务不可用时同样降级占位图。
    """

    def __init__(self):
        self.api_url = getattr(settings, 'SD_API_URL', 'http://127.0.0.1:7860/sdapi/v1/txt2img')
        self.used_fallback = False
        self.last_error = ''

    def generate_image(self, prompt, negative_prompt='', width=512, height=768, **kwargs):
        self.used_fallback = False
        payload = {
            'prompt': prompt,
            'negative_prompt': negative_prompt or '',
            'width': width,
            'height': height,
            'steps': kwargs.get('steps', 20),
            'cfg_scale': kwargs.get('cfg_scale', 7),
            'sampler_name': kwargs.get('sampler_name', 'Euler a'),
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            images = data.get('images') or []
            if not images:
                raise ValueError('SD 接口未返回图片')
            content = base64.b64decode(images[0])
            return True, _bytes_to_contentfile(content, width, height, 'sd')
        except Exception as e:
            self.used_fallback = True
            self.last_error = str(e)
            logger.warning('Stable Diffusion 调用失败（%s），降级为占位图：%s', self.api_url, e)
            return _gradient_fallback(width, height)

    def check_api_status(self):
        try:
            resp = requests.get(self.api_url.rsplit('/sdapi/', 1)[0] + '/sdapi/v1/sd-models', timeout=3)
            return resp.status_code == 200
        except Exception:
            return False


def get_image_generator():
    """按配置返回图像生成器（双后端切换入口）"""
    backend = getattr(settings, 'IMAGE_BACKEND', 'zhipu')
    if backend == 'sd':
        return SDImageGenerator()
    return CogViewImageGenerator()


class MockImageGenerator:
    """保留用于测试，生成渐变占位图"""

    def generate_image(self, prompt, negative_prompt='', width=512, height=768, **kwargs):
        import random
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        for i in range(width):
            for j in range(height):
                pixels[i, j] = (255, int(160 - 60 * (j / height)), int(100 - 50 * (j / height)))
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f'mock_{int(time.time())}_{random.randint(1000, 9999)}.png'
        return True, ContentFile(buffer.getvalue(), name=filename)
