"""
图像生成器
集成智谱 CogView-3-Flash API
"""
import io
import time
import requests
from PIL import Image
from django.core.files.base import ContentFile
from django.conf import settings


class CogViewImageGenerator:
    """基于智谱 CogView-3-Flash 的图像生成器"""

    # CogView-3-Flash 支持的尺寸，选最接近目标比例的
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

    def generate_image(self, prompt, negative_prompt='', width=512, height=768, **kwargs):
        """
        生成图像
        :param prompt: 提示词（SD 风格关键词或自然语言均可）
        :param negative_prompt: 负面提示词（CogView 不支持，忽略）
        :param width: 目标宽度
        :param height: 目标高度
        :return: (success, ContentFile) 或 (False, error_str)
        """
        if not self.api_key:
            return self._fallback_image(width, height)

        size = self.SIZE_MAP.get((width, height), self.DEFAULT_SIZE)
        cogview_prompt = self._convert_prompt(prompt)

        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=self.api_key)
            response = client.images.generations(
                model=self.model,
                prompt=cogview_prompt,
                size=size,
            )
            image_url = response.data[0].url
            return self._download_image(image_url, width, height)
        except Exception:
            return self._fallback_image(width, height)

    def _convert_prompt(self, prompt):
        """将 SD 风格关键词提示词转换为适合 CogView 的中文自然语言描述"""
        # 内容类型映射
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

        # 风格映射
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

        # 色彩映射
        color_map = {
            'warm colors, red, orange, yellow, cozy, inviting': '暖色调，红橙黄配色',
            'cool colors, blue, green, purple, calm, professional': '冷色调，蓝绿紫配色',
            'neutral colors, beige, gray, brown, balanced, versatile': '中性色调，米灰棕配色',
            'vibrant, saturated colors, bright, eye-catching, bold': '高饱和度，色彩鲜亮夺目',
            'monochrome, black and white, grayscale, elegant, classic': '黑白单色，经典雅致',
            'pastel colors, soft pink, light blue, mint, gentle, soothing': '马卡龙色，柔和粉嫩',
        }

        # 年龄特征映射
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

        # 去掉 SD 专用质量标签
        import re
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

        # 清理残余英文单词和多余标点
        desc = re.sub(r'[a-zA-Z]{3,}', '', desc)  # 去掉3字母以上英文
        desc = re.sub(r'[,，\s]+', '，', desc)
        desc = re.sub(r'，+', '，', desc)
        desc = desc.strip('，, ')

        if not desc or len(desc) < 5:
            desc = '现代时尚风格，色彩丰富'

        return f"一张精美的海报背景图，{desc}，画面精致，色彩丰富，构图美观，高清质感"

    def _download_image(self, url, width, height):
        """下载 URL 图片并转为 ContentFile，同时缩放到目标尺寸"""
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert('RGB')
            img = img.resize((width, height), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            filename = f'cogview_{int(time.time())}.png'
            return True, ContentFile(buffer.getvalue(), name=filename)
        except Exception as e:
            return False, f'图片下载失败: {e}'

    def _fallback_image(self, width, height):
        """无 API key 或调用失败时返回渐变占位图"""
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
        return True, ContentFile(buffer.getvalue(), name=f'placeholder_{int(time.time())}.png')

    def check_api_status(self):
        return bool(self.api_key)


class MockImageGenerator:
    """保留用于测试，生成渐变占位图"""

    def generate_image(self, prompt, negative_prompt='', width=512, height=768, **kwargs):
        import random
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        for i in range(width):
            for j in range(height):
                r = int(255)
                g = int(160 - 60 * (j / height))
                b = int(100 - 50 * (j / height))
                pixels[i, j] = (r, g, b)
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f'mock_{int(time.time())}_{random.randint(1000,9999)}.png'
        return True, ContentFile(buffer.getvalue(), name=filename)
